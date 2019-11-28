FROM python:3.8

WORKDIR /tpf2

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

COPY static static
COPY client client
COPY server server
COPY config.py ./

ENV SERVER_URL https://tpf-server.crazyideas.co.in/

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --access-logfile - --error-logfile - client:tpf2_app
