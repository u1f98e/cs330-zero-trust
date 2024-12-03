import datetime
import itertools
from typing import Dict

from zt_host.auth import ZTAuth
from zt_host.wireguard import Peer, ZTDevice


class Session:
    peer_addr: str
    pub_key: str
    expiration: datetime

class ZTSessionManager:
    incoming: Dict[str, Session] = {}
    outgoing: Dict[str, Session] = {}
    wg: ZTDevice

    def __init__(self, wg: ZTDevice):
        self.wg = wg

    def add_incoming(self, peer: Peer, expiration: int = None):
        session = Session()
        session.peer_addr = peer.endpoint_addr
        session.pub_key = peer.public_key
        session.expiration = expiration

        if session.peer_addr in self.incoming.keys():
            self.wg.remove_peer(self.incoming[session.peer_addr].pub_key)
            del self.incoming[session.peer_addr]

        self.incoming[session.peer_addr] = session
        self.wg.add_peer(peer)

    def add_outgoing(self, peer: Peer, expiration: int = None):
        session = Session()
        session.peer_addr = peer.endpoint_addr
        session.pub_key = peer.public_key
        session.expiration = expiration

        if session.peer_addr in self.outgoing.keys():
            self.wg.remove_peer(self.outgoing[session.peer_addr].pub_key)
            del self.outgoing[session.peer_addr]

        self.outgoing[session.peer_addr] = session
        self.wg.add_peer(peer)

    def expire_incoming(self):
        def f(session: Session):
            if session.expiration < now:
                print(f"DBG: Expiring session for {session.peer_addr}") 
                self.wg.remove_peer(session.pub_key) 
                return False
            else:
                return True

        now = datetime.datetime.now()
        self.incoming[:] = itertools.filterfalse(f, self.incoming)
    
    # TODO: Call this automatically with sched or similar
    def refresh_outgoing(self, auth: ZTAuth, peer_addr: str):
        session = self.outgoing[peer_addr]
        token = auth.request_refresh_token(session.peer_addr)
        # TODO: Send to client
        return
