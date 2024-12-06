#!/bin/bash
NETWORK_ADDR=192.168.99.3/24
WIREGUARD_ADDR=10.0.0.3/24
# AUTH_SERVER=192.168.99.10
AUTH_SERVER=localhost

ip addr add $NETWORK_ADDR dev eth0

killall python3 2> /dev/null
python3 -u /root/zt-host/main.py listen $WIREGUARD_ADDR $AUTH_SERVER > client.log 2>&1 &
sleep 2
if [[ "$(ps | grep $!)" ]]; then
	echo "Now listening with private address $WIREGUARD_ADDR"
else
	echo "Shutdown too early, please check client.log"
	cat client.log
fi
