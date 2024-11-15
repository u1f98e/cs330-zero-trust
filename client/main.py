import socket
import threading
import json
import jwt
import sys

from zt_host.wireguard import WireguardDevice, Peer

MAX_MESSAGE_SIZE=4096
TOKEN_PUBLIC_KEY = ""

class ZtContext:
    wg: WireguardDevice

    def __init__(_wg: WireguardDevice):
        wg = _wg

def handle_connect_request(token: str, ctx: ZtContext):
    # decoded = jwt.decode(token, key=TOKEN_PUBLIC_KEY, algorithms=['RS256',])
    decoded = token
    peer_nickname = decoded["nick"]
    peer_pub_key = decoded["wg_pub"]

    peer = Peer()
    peer.nickname = decoded["name"]
    peer.public_key = decoded["wg_pub"]
    ctx.wg.add_peer()

def process_peer_message(data: str, ctx: ZtContext):
    msg = json.load(data)
    if msg["type"] == "connect":
        handle_connect_request(msg.jwt)

# Listen for new peer connection requests,
# validating the request's JWT token and opening
# a new tunnel if successful.
def listen_for_peers(host, port, ctx: ZtContext):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((host, port))
    server.listen(0)
    while True:
        try:
            connection, client_addr = server.accept()
            reader = connection.makefile(buffering=1, encoding='utf-8')

            while True:
                data: str = reader.readline(MAX_MESSAGE_SIZE)
                if not data:
                    break
                process_peer_message(data, ctx)

        except Exception as e:
            print(f"Error while processing message: {e}")

def daemon_main():
    # Create wireguard interface
    wg = WireguardDevice.create("wgTest0")
    ctx = ZtContext(wg)

    try:
        peer_listen_args = ("127.0.0.1", 9090, ctx)
        # threading.Thread(target=listen_for_peers, args=peer_listen_args)
        listen_for_peers(*peer_listen_args)
        print("Hi")
    finally:
        wg.close()

def _help():
    print("zt-host [connect <peer-ip>]")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "help":
            _help()
        if sys.argv[1] == "connect":
            peer_ip = sys.argv[2]
            request_connection(peer_ip)
    
    daemon_main()
