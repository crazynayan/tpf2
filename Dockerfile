FROM python:3.8

WORKDIR /tpf2

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

COPY flask_app flask_app
COPY config.py google-cloud-tokyo.json ./

ENV SERVER_URL https://tpf-server-tokyo.crazyideas.co.in/
ENV GOOGLE_APPLICATION_CREDENTIALS google-cloud-tokyo.json

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --access-logfile - --error-logfile - flask_app:tpf2_app
