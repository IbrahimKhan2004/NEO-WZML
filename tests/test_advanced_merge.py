import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from web.advanced_merge_store import (
    write_state,
    read_state,
    save_groups,
    get_groups,
    get_file_list,
    get_merge_data,
    delete_state,
)
from web.wserver import app
from bot.helper.mirror_leech_utils.status_utils.merge_status import AdvancedMergeStatus


class TestAdvancedMergeStore(unittest.TestCase):
    def setUp(self):
        self.gid = "test_gid_123"
        self.sample_files = [
            {"path": "Achinta.Trial.By.Law.Hindi.S03.480p/E01.mkv", "size": 1000},
            {"path": "Achinta.Trial.By.Law.Hindi.S03.480p/E02.mkv", "size": 2000},
        ]

    def tearDown(self):
        delete_state(self.gid)

    def test_store_operations(self):
        # 1. Write state
        ok = write_state(self.gid, self.sample_files)
        self.assertTrue(ok)

        # 2. Read state
        state = read_state(self.gid)
        self.assertIsNotNone(state)
        self.assertEqual(state["files"], self.sample_files)

        # 3. Get file list
        files = get_file_list(self.gid)
        self.assertEqual(files, self.sample_files)

        # 4. Save groups
        groups = [
            {
                "output_name": "Merged_Video_1.mp4",
                "files": ["Achinta.Trial.By.Law.Hindi.S03.480p/E01.mkv"],
            }
        ]
        ok_save = save_groups(self.gid, groups)
        self.assertTrue(ok_save)

        # 5. Get groups
        retrieved_groups = get_groups(self.gid)
        self.assertEqual(retrieved_groups, groups)

        # 6. Get merge data
        data = get_merge_data(self.gid)
        self.assertEqual(data["files"], self.sample_files)
        self.assertEqual(data["groups"], groups)


class TestAdvancedMergeStatus(unittest.TestCase):
    def test_advanced_merge_status_methods(self):
        listener = MagicMock()
        listener.name = "Test_Task.mkv"
        listener.size = 10485760  # 10 MB
        gid = "test_gid_789"

        status_obj = AdvancedMergeStatus(listener, gid)

        self.assertEqual(status_obj.gid(), gid)
        self.assertEqual(status_obj.progress(), "0%")
        self.assertEqual(status_obj.speed(), "0B/s")
        self.assertEqual(status_obj.processed_bytes(), "0B")
        self.assertEqual(status_obj.name(), "Test_Task.mkv")
        self.assertEqual(status_obj.size(), "10.00MB")
        self.assertEqual(status_obj.eta(), "-")
        self.assertEqual(status_obj.status(), "Waiting for User")


class TestAdvancedMergeWserver(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.gid = "web_test_gid_456"
        self.sample_files = [
            {"path": "Achinta.Trial.By.Law.Hindi.S03.480p.AMZN.WEB-DL.Hindi.AAC2.0.H.264-ExtraFlix.Pw/E01.mkv", "size": 66790000},
            {"path": "Achinta.Trial.By.Law.Hindi.S03.480p.AMZN.WEB-DL.Hindi.AAC2.0.H.264-ExtraFlix.Pw/E02.mkv", "size": 65300000},
        ]
        write_state(self.gid, self.sample_files)

    def tearDown(self):
        delete_state(self.gid)

    def test_get_merge_files_endpoint(self):
        response = self.client.get(f"/app/merge/files?gid={self.gid}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("files", data)
        self.assertEqual(len(data["files"]), 2)
        self.assertTrue(data["files"][0]["path"].startswith("Achinta.Trial.By.Law.Hindi.S03.480p"))

    def test_submit_merge_endpoint(self):
        payload = {
            "groups": [
                {
                    "output_name": "Merged_Video_1.mp4",
                    "files": [
                        "Achinta.Trial.By.Law.Hindi.S03.480p.AMZN.WEB-DL.Hindi.AAC2.0.H.264-ExtraFlix.Pw/E01.mkv",
                        "Achinta.Trial.By.Law.Hindi.S03.480p.AMZN.WEB-DL.Hindi.AAC2.0.H.264-ExtraFlix.Pw/E02.mkv",
                    ],
                }
            ]
        }
        response = self.client.post(f"/app/merge/submit?gid={self.gid}", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # Check saved groups
        saved_groups = get_groups(self.gid)
        self.assertEqual(len(saved_groups), 1)
        self.assertEqual(saved_groups[0]["output_name"], "Merged_Video_1.mp4")


class TestPathRelativity(unittest.TestCase):
    def test_folder_download_path_resolution(self):
        temp_dir = tempfile.mkdtemp()
        try:
            folder_name = "Achinta.Trial.By.Law.Hindi.S03.480p.AMZN.WEB-DL.Hindi.AAC2.0.H.264-ExtraFlix.Pw"
            dl_path = os.path.join(temp_dir, folder_name)
            os.makedirs(dl_path, exist_ok=True)
            file_name = "Achinta.Trial.By.Law.Hindi.S03E01.480p.AMZN.WEB-DL.Hindi.AAC2.0.H.264-ExtraFlix.Pw.mkv"
            full_file_path = os.path.join(dl_path, file_name)
            with open(full_file_path, "w") as f:
                f.write("dummy")

            parent_dir = os.path.dirname(dl_path)
            rel_path = os.path.relpath(full_file_path, parent_dir)
            expected_rel_path = os.path.join(folder_name, file_name)

            self.assertEqual(rel_path, expected_rel_path)

            reconstructed_path = os.path.join(parent_dir, rel_path)
            self.assertEqual(reconstructed_path, full_file_path)
            self.assertTrue(os.path.exists(reconstructed_path))
        finally:
            shutil.rmtree(temp_dir)

    def test_single_file_download_path_resolution(self):
        temp_dir = tempfile.mkdtemp()
        try:
            file_name = "sample_video.mkv"
            dl_path = os.path.join(temp_dir, file_name)
            with open(dl_path, "w") as f:
                f.write("dummy")

            parent_dir = os.path.dirname(dl_path)
            rel_path = os.path.relpath(dl_path, parent_dir)

            self.assertEqual(rel_path, file_name)

            reconstructed_path = os.path.join(parent_dir, rel_path)
            self.assertEqual(reconstructed_path, dl_path)
            self.assertTrue(os.path.exists(reconstructed_path))
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
