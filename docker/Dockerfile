FROM python:3.6-slim

ADD pip_requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

ADD ../src/*.py /app/
ADD ../pickle/ /app/pickle/
ADD ../www/static /app/static/

WORKDIR /app

EXPOSE 5000

CMD [ "python", "backend.py" ]
