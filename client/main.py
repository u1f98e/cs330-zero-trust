#!/usr/bin/env python3

import argparse
import sched
import socket
import threading
import json
import time
import jwt
import sys
from wireguard_tools import WireguardKey

from zt_host.session import ZTSessionManager
from zt_host.local_pipe import NamedPipe
from zt_host.auth import AUTH_PUBLIC_KEY, ZTAuth
from zt_host.wireguard import ZTDevice, Peer

MAX_MESSAGE_SIZE=4096
WIREGUARD_PORT = 8888
COMM_PORT = 8889
LOCAL_COMMAND_PIPE="/var/zt-local-pipe"
DEBUG = True

class ZtContext:
    wg: ZTDevice
    auth: ZTAuth
    scheduler: sched.scheduler
    sessions: ZTSessionManager
    name: str

    def __init__(self, _wg: ZTDevice, _auth: ZTAuth):
        self.wg = _wg
        self.auth = _auth
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.sessions = ZTSessionManager(self.wg)

    def expire_incoming_sessions(self):
        self.sessions.expire_incoming_sessions()

    def request_connection(self, peer_addr: str):
        """Authorize and request a connection to a peer"""
        if DEBUG:
            print(f"DBG: Requesting new connection to peer at {peer_addr}")

        # Open a socket to the peer so we know the laddr,
        # the local address used to communicate with it
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_sock.connect((peer_addr, COMM_PORT))
        local_addr, _ = peer_sock.getsockname()

        token = (self.auth.request_connection_token(
            peer_addr, 
            local_addr, 
            wg_addr = self.wg.wg_addr, 
            pub_key = self.wg.pub_key))

        request = {
            "type": "connect",
            "token": token.jwt
        }
        if DEBUG:
            print(f"DBG: Sending request {json.dumps(request)}")

        sock = peer_sock.makefile('rw')
        sock.write(json.dumps(request) + '\n')
        sock.flush()

        response = sock.readline(MAX_MESSAGE_SIZE)
        if DEBUG:
            print(f"Recieved: {response}")
        response = json.loads(response)
        # if "result" not in response:
        #     raise Exception("Response message from peer did not contain 'result' field")
        # if response["result"] != "ok":
        #     if "msg" in response:
        #         raise Exception(f"Peer returned an error during connection request: {response["msg"]}")
        #     else:
        #         raise Exception(f"Peer returned an error during connection request")

        pub_key = response['pub_key']
        peer_wg_addr = response['wg_addr']

        peer = Peer()
        peer.public_key = pub_key
        peer.endpoint_addr = peer_addr
        peer.endpoint_port = WIREGUARD_PORT
        peer.allowed_ips = [peer_wg_addr]
        self.sessions.add_outgoing(peer, token.expiration)

    def handle_connect_request(self, token: str, client_addr: str):
        if DEBUG:
            print("DBG: Handling connection request")
        decoded = jwt.decode(token, key=AUTH_PUBLIC_KEY, algorithms=['RS256',])
        if DEBUG:
            print(f"DBG: {decoded}")

        peer = Peer()
        peer.public_key = decoded["pub"]
        peer.endpoint_addr = decoded["addr"]
        peer.endpoint_port = WIREGUARD_PORT
        peer.allowed_ips = decoded["ips"].split(";")
        expiration = decoded["exp"]

        if client_addr != peer.endpoint_addr:
            print("Error: Failed to add new peer, connection address does not match endpoint address")
            if DEBUG:
                print(f"DBG: client_addr: {client_addr}")
                print(f"DBG: endpoint_addr: {peer.endpoint_addr}")
            return

        if DEBUG:
            print(f"DBG: Adding new peer {peer}")
        self.sessions.add_incoming(peer, expiration)

        # Schedule an expiration check when this session is supposed to expire
        self.scheduler.enterabs(expiration, 1, ZtContext.expire_incoming_sessions, argument=[self])

        return json.dumps({
            "pub_key": self.wg.pub_key,
            "wg_addr": self.wg.wg_addr
        })

    def process_peer_message(self, response_writer, data: str, client_addr: str):
        msg = json.loads(data)
        if msg["type"] == "connect":
            response = self.handle_connect_request(msg["token"], client_addr)
            response_writer.write(response + '\n')
            response_writer.flush()
        
    def process_peer_connection(self, sock: socket.socket, client_addr):
        if DEBUG:
            print(f"DBG: Peer connected from {client_addr}")
        reader = sock.makefile('r', buffering=1, encoding='utf-8')
        writer = sock.makefile('w', encoding='utf-8')

        while True:
            data: str = reader.readline(MAX_MESSAGE_SIZE)
            if not data:
                if DEBUG:
                    print(f"Empty command recieved, closing thread for {client_addr}")
                break

            if DEBUG:
                print(f"DBG: Got peer msg from {client_addr}: {data}")
            self.process_peer_message(writer, data, client_addr)

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
                connection, (client_addr, client_port) = server.accept()
                args = (connection, client_addr)
                thread = threading.Thread(target=self.process_peer_connection, args=args)
                thread.daemon = True
                thread.start()

            except Exception as e:
                raise Exception(f"Error while processing connection") from e

    def listen_local_commands(self):
        if DEBUG:
            print(f"DBG: Listening for local commands on {LOCAL_COMMAND_PIPE}")

        with NamedPipe(LOCAL_COMMAND_PIPE, 'r') as pipe:
            while True:
                try:
                    line = pipe.readline()
                    if not line:
                        if DEBUG:
                            print(f"DBG: Empty local command received, skipping")
                        continue

                    msg = json.loads(line)
                    if DEBUG:
                        print(f"DBG: Got local command: {msg}")

                    if msg["type"] == "connect":
                        self.request_connection(msg["peer_addr"])
                except Exception as e:
                    raise Exception(f"Exception while processing local command") from e
                    break

def daemon_main(args):
    private_key = WireguardKey.generate()

    if DEBUG:
        print("DBG: Creating wgTest0")
    wg = (
        ZTDevice.create("wgTest0", 
                        private_key = str(private_key),
                        public_key = str(private_key.public_key()),
                        wg_addr = args.listen_addr, # TODO: Get from auth server or something
                        listen_port = WIREGUARD_PORT,
                        force = True)
    )
    auth = ZTAuth((args.auth_addr, int(args.auth_port)))
    ctx = ZtContext(wg, auth)

    try:
        local_comm_thread = threading.Thread(target=ctx.listen_local_commands)
        local_comm_thread.daemon = True
        local_comm_thread.start()

        peer_listen_args = ("0.0.0.0", COMM_PORT)
        ctx.listen_for_peers(*peer_listen_args)
    finally:
        if DEBUG:
            print("DBG: Disabling wireguard device")
        wg.down()

def connect_subcommand(args):
    if DEBUG:
        print("DBG: Sending connection command")
    with NamedPipe(LOCAL_COMMAND_PIPE, 'w') as pipe:
        msg = json.dumps({
            "type": "connect",
            "peer_addr": args.peer_addr
        })
        print("DBG: " + msg)
        pipe.write(msg + '\n')

if __name__ == "__main__":
    if DEBUG:
        print("DBG: Starting peer daemon")
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
    if DEBUG:
        print("DBG: Subcommands setup")

    args = parser.parse_args(sys.argv[1:])
    if hasattr(args, "func"):
        args.func(args)