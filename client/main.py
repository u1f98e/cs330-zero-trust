import argparse
import datetime
import itertools
import os
import sched
import socket
import threading
import json
import time
from typing import Dict, List
import jwt
import sys
from wireguard_tools import WireguardKey

from zt_host.local_pipe import NamedPipe
from zt_host.auth import AUTH_PUBLIC_KEY, ZTAuth
from zt_host.wireguard import ZTDevice, Peer

MAX_MESSAGE_SIZE=4096
WIREGUARD_PORT = 8888
COMM_PORT = 8889
LOCAL_COMMAND_PIPE="/var/zt-local-pipe"
DEBUG = True

class Session:
    peer_addr: str
    peer_pub_key: str
    expiration: datetime

class ZtContext:
    wg: ZTDevice
    auth: ZTAuth
    scheduler: sched.scheduler
    name: str

    incoming_sessions: List[Session] = []
    outgoing_sessions: Dict[str, Session] = {}

    def __init__(self, _wg: ZTDevice, _auth: ZTAuth):
        self.wg = _wg
        self.auth = _auth
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def expire_incoming_sessions(self):
        def f(session: Session):
            if session.expiration < now:
                if DEBUG:
                    print(f"DBG: Expiring session for {session.peer_addr}") 
                self.wg.remove_peer(session.peer_pub_key) 
                return False
            else:
                return True

        now = datetime.datetime.now()
        self.incoming_sessions[:] = itertools.filterfalse(f, self.incoming_sessions)
    
    # TODO: Call this automatically with sched or similar
    def refresh_session(self, peer_pub_key: str):
        session = self.outgoing_sessions[peer_pub_key]
        token = self.auth.request_refresh_token(session.peer_addr)
        # TODO: Send to client
        return

    def request_connection(self, peer_addr: str):
        """Authorize and request a connection to a peer"""
        if DEBUG:
            print(f"DBG: Requesting new connection to peer at {peer_addr}")

        # Open a socket to the peer so we know the laddr,
        # the local address used to communicate with it
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_sock.connect((peer_addr, COMM_PORT))
        local_addr, _ = peer_sock.getsockname()

        token = self.auth.request_connection_token(peer_addr, local_addr, self.wg.pub_key)

        request = {
            "type": "connect",
            "token": token.jwt
        }

        s = peer_sock.makefile('rw')
        s.write(json.dumps(request) + '\n')
        response = json.loads(s.readline(MAX_MESSAGE_SIZE))
        if "result" not in response:
            raise Exception("Response message from peer did not contain 'result' field")
        if response["result"] != "ok":
            if "msg" in response:
                raise Exception(f"Peer returned an error during connection request: {response["msg"]}")
            else:
                raise Exception(f"Peer returned an error during connection request")

        session = Session()
        session.peer_addr = peer_addr
        session.peer_pub_key = response['pub_key']
        session.expiration = token.expiration
        self.outgoing_sessions[session.peer_pub_key] = session

    def handle_connect_request(self, token: str, client_addr: str):
        decoded = jwt.decode(token, key=AUTH_PUBLIC_KEY, algorithms=['RS256',])
        decoded = json.load(token)

        peer = Peer()
        peer.name = decoded["name"]
        peer.public_key = decoded["pub"]
        peer.endpoint_addr = decoded["addr"]
        peer.endpoint_port = WIREGUARD_PORT
        peer.allowed_ips = decoded["ips"]
        expiration = decoded["exp"]

        if client_addr != peer.endpoint_addr:
            print("Error: Failed to add new peer, connection address does not match endpoint address")
            return

        self.wg.add_peer(peer)

        session = Session()
        session.expiration = expiration
        session.peer_pub_key = peer.public_key
        session.peer_addr = peer.endpoint_addr
        self.incoming_sessions.append(session)

        # Schedule an expiration check when this session is supposed to expire
        self.scheduler.enterabs(expiration, 1, ZtContext.expire_incoming_sessions, argument=[self])

    def process_peer_message(self, data: str, client_addr: str):
        msg = json.load(data)
        if msg["type"] == "connect":
            self.handle_connect_request(msg.jwt, client_addr)

    # Listen for new peer connection requests,
    # validating the request's JWT token and opening
    # a new tunnel if successful.
    def listen_for_peers(self, host, port):
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

                    args = (data, client_addr)
                    if DEBUG:
                        print(f"DBG: Got peer msg from {client_addr}: {data}")
                    threading.Thread(target=self.process_peer_message, args=args).start()

            except Exception as e:
                print(f"Error while processing message: {e}")

    def listen_local_commands(self):
        if DEBUG:
            print(f"DBG: Listening for local commands on {LOCAL_COMMAND_PIPE}")

        with NamedPipe(LOCAL_COMMAND_PIPE, 'r') as pipe:
            while True:
                msg = json.loads(pipe.readline())

                if DEBUG:
                    print(f"DBG: Got local command: {msg}")

                if msg["type"] == "connect":
                    self.request_connection(msg["peer_addr"])

def daemon_main(args):
    private_key = WireguardKey.generate()
    wg = (
        ZTDevice.create("wgTest0", 
                        private_key = str(private_key),
                        public_key = str(private_key.public_key()),
                        wg_addr = args.listen_addr, # TODO: Get from auth server or something
                        listen_port = WIREGUARD_PORT)
    )
    auth = ZTAuth((args.auth_addr, int(args.auth_port)))
    ctx = ZtContext(wg, auth)

    try:
        threading.Thread(target=ctx.listen_local_commands).start()

        peer_listen_args = ("0.0.0.0", COMM_PORT)
        # threading.Thread(target=ctx.listen_for_peers, args=peer_listen_args)
        ctx.listen_for_peers(*peer_listen_args)
    finally:
        wg.down()

def connect_subcommand(args):
    print("DBG: Sending connection command")
    with NamedPipe(LOCAL_COMMAND_PIPE, 'w') as pipe:
        msg = json.dumps({
            "type": "connect",
            "peer_addr": args.peer_addr
        })
        print("DBG: " + msg)
        pipe.write(msg + '\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="zt-host",
    )

    subcommands = parser.add_subparsers(required=True)
    listen_sub = subcommands.add_parser("listen")
    listen_sub.add_argument("listen_addr", help="The address for this host's wireguard tunnel")
    listen_sub.add_argument("auth_addr", help="The address for the root auth node")
    listen_sub.add_argument("auth_port", default="8080", nargs="?", help="The port for the root auth node")
    listen_sub.set_defaults(func=daemon_main)

    connect_sub = subcommands.add_parser("connect")
    connect_sub.set_defaults(func=connect_subcommand)
    connect_sub.add_argument("peer_addr", help="The address for the peer on the physical network")

    args = parser.parse_args(sys.argv[1:])
    if hasattr(args, "func"):
        args.func(args)