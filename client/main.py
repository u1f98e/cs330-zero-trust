import datetime
import itertools
import socket
import threading
import json
from typing import List
import jwt
import sys
from wireguard_tools import WireguardKey

from zt_host.auth import ZTAuth, PeerAuthToken
from zt_host.wireguard import ZTDevice, Peer

MAX_MESSAGE_SIZE=4096
WIREGUARD_PORT = 8888
COMM_PORT = 8889

class Session:
    peer_addr: str
    peer_pub_key: str
    expiration: datetime

class ZtContext:
    wg: ZTDevice
    auth: ZTAuth
    name: str
    pub_key: str

    incoming_sessions: List[Session] = []
    outgoing_sessions: List[Session] = []

    def __init__(self, _wg: ZTDevice):
        self.wg = _wg

    def expire_incoming(self):
        def f(session: Session):
            if session.expiration < now:
               self.wg.remove_peer(session.peer_pub_key) 
               return False
            else:
                return True

        now = datetime.datetime.now()
        self.incoming_sessions[:] = itertools.filterfalse(f, self.incoming_sessions)

    def refresh_session(self, peer_addr: str):
        for session in self.outgoing_sessions:
            if session.peer_addr == peer_addr:
                token = self.auth.request_refresh_token()

    def send_connect_request(peer_addr: str, token: PeerAuthToken):
        # Open a socket to the peer so we know the laddr,
        # the local address used to communicate with it
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_sock.bind((peer_addr, COMM_PORT))
        local_addr, _ = peer_sock.getsockname()

        request = {
            "type": "connect",
            "token": token.jwt
        }

        peer_sock.sendall(json.dumps(request) + '\n')

    def request_connection(self, peer_addr: str):
        """Authorize and request a connection to a peer"""
        # Open a socket to the peer so we know the laddr,
        # the local address used to communicate with it
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_sock.bind((peer_addr, COMM_PORT))
        local_addr, _ = peer_sock.getsockname()

        token = self.auth.request_connection_token(peer_addr, local_addr)

        # TODO: This is a fake token for now
        token.jwt = { 
            "name": self.name, 
            "wg_pub": self.pub_key,
            "addr": local_addr,
            "ips": [local_addr],
        }
        print(token.jwt)

        request = {
            "type": "connect",
            "token": token.jwt
        }

        peer_sock.sendall(json.dumps(request) + '\n')

def handle_connect_request(token: str, client_addr: str, ctx: ZtContext):
    # decoded = jwt.decode(token, key=TOKEN_PUBLIC_KEY, algorithms=['RS256',])
    decoded = json.load(token)

    peer = Peer()
    peer.name = decoded["name"]
    peer.public_key = decoded["wg_pub"]
    peer.endpoint_addr = decoded["addr"]
    peer.endpoint_port = WIREGUARD_PORT
    peer.allowed_ips = decoded["ips"]

    if client_addr != peer.endpoint_addr:
        print("Error: Failed to add new peer, connection address does not match endpoint address")
        return

    ctx.wg.add_peer(peer)

def process_peer_message(data: str, client_addr: str, ctx: ZtContext):
    msg = json.load(data)
    if msg["type"] == "connect":
        handle_connect_request(msg.jwt, client_addr)

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

                args = (data, client_addr, ctx)
                threading.Thread(target=process_peer_message, args=args)

        except Exception as e:
            print(f"Error while processing message: {e}")

def daemon_main():
    private_key = WireguardKey.generate()
    wg = (
        ZTDevice.create("wgTest0", 
                        private_key = str(private_key),
                        public_key = str(private_key.public_key()),
                        wg_addr = '10.0.0.2',
                        listen_port = WIREGUARD_PORT)
    )

    ctx = ZtContext(wg)

    try:
        peer_listen_args = ("localhost", COMM_PORT, ctx)
        # threading.Thread(target=listen_for_peers, args=peer_listen_args)
        listen_for_peers(*peer_listen_args)
        print("Hi")
    finally:
        wg.down()

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
