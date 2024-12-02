FROM docker.io/python:3.13-bookworm
RUN apt update && \
	DEBIAN_FRONTEND=noninteractive apt install -y iproute2 net-tools iputils-ping vim nano tmux psmisc

RUN mkdir -p /root/zt-host
WORKDIR /root/zt-host

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install pyrasite

ADD main.py main.py
ADD zt_host zt_host
ADD scripts scripts

# CMD ["python3", "/root/zt-host/main.py"]
CMD ["/bin/bash"]