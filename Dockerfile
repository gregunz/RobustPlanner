FROM python:3.6-slim

ADD pip_requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

ADD . /app
ADD pickle /app/pickle
ADD data/metadata/BFKOORD_GEO /app/data/metadata/BFKOORD_GEO 


WORKDIR /app

EXPOSE 5000

CMD [ "python", "backend.py" ]
