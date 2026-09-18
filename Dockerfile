# This file is a part of NEO-WZML (github.com/IbrahimKhan2004/NEO-WZML)

FROM irisxdr/neo-wzml:latest

WORKDIR /usr/src/app

RUN chmod 777 /usr/src/app

COPY requirements.txt .
RUN uv pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash", "start.sh"]
