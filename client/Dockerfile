FROM docker.io/python:3.13-bookworm
RUN apt update && \
	DEBIAN_FRONTEND=noninteractive apt install -y iproute2 net-tools iputils-ping vim nano tmux

RUN mkdir -p /root/zt-host
WORKDIR /root/zt-host

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD main.py main.py
ADD zt_host zt_host

CMD ["python3", "/root/zt-host/main.py"]