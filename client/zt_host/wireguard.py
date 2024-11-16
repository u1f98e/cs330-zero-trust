import subprocess
from pyroute2 import IPRoute
from typing import Self, List, Tuple

class DeviceConfig:
	listen_port: int = None
	private_key: str = None

class Peer:
	name: str
	public_key: str
	allowed_ips: List[str]
	endpoint_ip: str

class WireguardDevice:
	_name: str
	_addr: str
	_mask: int

	def up(interface_name: str) -> Self:
		dev = WireguardDevice()
		dev._name = interface_name
		dev._addr = "10.5.0.1"
		dev._mask = 24

		ip = IPRoute()
		ip.addr("add", address=dev._addr, mask=dev._mask, label=dev._name)

		return dev

	def add_peer(self, peer: Peer):
		params = []
		params += ["public-key", peer.public_key]
		params += ["allowed-ips", peer.allowed_ips]
		params += ["endpoint", peer.endpoint_ip]
		subprocess.run(["wg", "set", self._name, "peer"] + params)

	def remove_peer(self, public_key: str):
		subprocess.run(["wg", "set", self._name, "peer", public_key, "remove"])

	def set_config(self, config: DeviceConfig):
		params = []
		if config.listen_port != None:
			params += ["listen-port", config.listen_port]
		if config.private_key:
			params += ["private-key", config.private_key]

		subprocess.run(["wg", "set", self._name] + params)

	def down(self):
		ip = IPRoute()
		ip.addr("delete", address=self._addr, mask=self._mask, label=self._name)
