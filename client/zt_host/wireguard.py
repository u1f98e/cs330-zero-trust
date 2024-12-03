import datetime
import subprocess
from pyroute2 import IPRoute, NDB, WireGuard
from typing import Self, List, Tuple

class Peer:
    # Device config fields, required by pyroute2
    public_key: str # The peer's wireguard public key
    endpoint_addr: str # The endpoint address (address of the real interface for this peer)
    endpoint_port: int # The endpoint port
    allowed_ips: str # List of CIDR address/subnets that we forward to this peer
    persistent_keepalive: int = 15

    # Extra fields
    name: str
    expiration: datetime # After this timestamp, this peer is invalid and should be discarded

class ZTDevice:
    ifname: str
    wg_addr: str # The address for this device within the wireguard network
    listen_port: int # The port which this device will use for wireguard connections
    pub_key: str

    def create(ifname: str, public_key: str, private_key: str, wg_addr: str, listen_port: int, force: bool = False) -> Self:
        dev = ZTDevice()
        dev.ifname = ifname
        dev.wg_addr = wg_addr
        dev.listen_port = listen_port
        dev.pub_key = public_key

        with NDB() as ndb:
            if dev.ifname in ndb.interfaces and not force:
                print(f"Using existing network device '{dev.ifname}'")
                (ndb.interfaces[dev.ifname]
                    .set(state='up')
                    .commit()
                )
            else:
                if dev.ifname in ndb.interfaces:
                    print(f"Removing existing device {dev.ifname}")
                    ndb.interfaces[dev.ifname].remove().commit()

                print(f"Creating new network device '{dev.ifname}'")
                (ndb.interfaces.create(kind='wireguard', ifname=dev.ifname) 
                    .add_ip(dev.wg_addr)
                    .set(state='up')
                    .commit()
                )

        with WireGuard() as wg:
            wg.set(dev.ifname, private_key=private_key, fwmark=0xf98e, listen_port=listen_port)

        return dev

    def get(ifname: str) -> Self:
        dev = ZTDevice()
        dev.ifname = ifname

        with NDB() as ndb:
            if ifname not in ndb.interfaces:
                raise Exception(f"Device '{ifname}' does not exist.")
            with WireGuard() as wg:
                info = wg.info(ifname)

                dev.wg_addr = info[0].get()
                dev.listen_port = info[0].get()

        return dev

    def add_peer(self, peer: Peer):
        peer_dict = peer.__dict__
        with WireGuard() as wg:
            print(f"DBG: {self.ifname}")
            output = "\n".join("{0} {1}".format(k, v)  for k,v in peer_dict.items())
            print(f"DBG: {output}")

            wg.set(self.ifname, peer=peer_dict)	

    def remove_peer(self, public_key: str):
        peer = {'public_key': public_key,
                'remove': True}

        with WireGuard() as wg:
            wg.set(self.ifname, peer=peer)	

    def up(self):
        with NDB() as ndb:
            link = ndb.interfaces[self.ifname]
            link.set(state='up')

    def down(self):
        with NDB() as ndb:
            link = ndb.interfaces[self.ifname]
            link.set(state='down')

    def remove(self):
        with NDB() as ndb:
            ndb.interfaces[self.ifname].remove()


