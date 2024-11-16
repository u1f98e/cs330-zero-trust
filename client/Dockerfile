FROM docker.io/python:3.13-bookworm

RUN mkdir -p /root/zt-host
WORKDIR /root/zt-host

ADD main.py main.py
ADD requirements.txt requirements.txt
ADD zt_host zt_host

RUN pip install -r requirements.txt

CMD ["python3", "/root/zt-host/main.py"]