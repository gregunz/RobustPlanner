FROM python:3.6-slim

ADD pip_requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

ADD ../src/ /app/src/
ADD ../pickle/ /app/pickle/
ADD ../www/ /app/www/

WORKDIR /app/www/

EXPOSE 5000

CMD [ "python", "backend.py" ]
