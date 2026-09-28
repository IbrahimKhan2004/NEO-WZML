# This file is a part of NEO-WZML (github.com/IbrahimKhan2004/NEO-WZML)

from functools import lru_cache
from pycountry import languages
from langcodes import Language


@lru_cache(maxsize=2048)
def get_native_lang(lang_code_or_name, fallback=""):
    if not lang_code_or_name or str(lang_code_or_name).lower() in {
        "unknown",
        "und",
        "none",
    }:
        return fallback or lang_code_or_name

    code_to_try = str(lang_code_or_name).strip()
    try:
        if len(code_to_try) == 2:
            lang_obj = languages.get(alpha_2=code_to_try.lower())
        elif len(code_to_try) == 3:
            lang_obj = languages.get(alpha_3=code_to_try.lower())
        else:
            lang_obj = languages.get(name=code_to_try)
        if lang_obj:
            code_to_try = (
                getattr(lang_obj, "alpha_2", None)
                or getattr(lang_obj, "alpha_3", None)
                or code_to_try
            )
    except Exception:
        pass

    try:
        autonym = Language.get(code_to_try).autonym()
        if autonym:
            return autonym
    except Exception:
        pass

    return fallback or lang_code_or_name
