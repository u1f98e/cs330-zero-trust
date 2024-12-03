# Zero Trust Experiment

# Setup

## Authentication Servers
For our authentication server, we use [Keycloak](https://keycloak.org). 

### Combined Docker Image (GNS3)
A Dockerfile is provided to build a combined Keycloak/PostgreSQL image for use 
in GNS3 as a node. To build it:

```
cd keycloak
docker build . --tag zt-keycloak
```

Then, you should be able to choose the `zt-keycloak` image in GNS3 to create a 
docker node.

From within GNS3, you can edit the docker image to add
a volume mount at `/var/db` to avoid needing to set up
the database each time the container starts.

You can access the Keycloak admin console at: http://localhost:8080

### Docker Compose
For deployment on a full system, prefer using [docker compose](https://docs.docker.com/compose/install/).
To start a keycloak instance, you can use the provided compose-root.yml
file:

```bash
cd keycloak
docker-compose -f compose-root.yml up 

# To shut down the containers
docker-compose -f compose-root.yml down
```

You should then be able to access the Keycloak admin console and the
pgAdmin database consoles. Default credentials can be found in the compose file.

- Keycloak admin console: http://localhost:8080
- Database admin console: http://localhost:8081

### Caching

Keycloak supports multiple cache servers using the [Infinispan](https://infinispan.org/docs/stable/titles/configuring/configuring.html) 
cache setting:

```
./kc.sh start --cache=ispn
```

We use the `invalidation` mode for caching, which should propagate writes from
the root server (writes generally should be infrequent)

TODO: How do cache servers get specified/discovered?

## Tunnel Client
Our custom host to host client uses wireguard to form secure tunnels between hosts.

A Dockerfile is also provided for running the client as a GNS3 device:

```bash
cd client
docker build . --tag zt-host
```

## Host Demo
Two scripts are provided in `client/scripts` which can set up 
two docker hosts for a demonstration. The scripts set an
address on `eth0` (`192.168.1.2` for host1 and `192.168.1.3` for host2), and then start the client program.

If both of the clients start successfully (you can check `client.log` for errors), on one of the hosts run:

```bash
./main.py connect <real peer address (like 192.168.1.3)>
```

> Note: The current demo always connects, as it does not currently support authentication.

After a successful connection, if you have `wireguard-tools` installed you can use the `wg` command to verify a peer has been added:

```bash
$ wg
interface: wgTest0
  public key: iWmztSc0yWiiWV+C/pPurRqkmmLcI0TFXs5LpT+S+C8=
  private key: (hidden)
  listening port: 8888
  fwmark: 0xf98e

peer: FPQ2iEKFF8ZN3Hf2/bfGR2a7MrlnVZOKvakSpRtNngI=
  endpoint: 192.168.1.3:8888
  allowed ips: 10.0.0.0/24
```

Wireguard peers form a private network between devices (the demo scripts set host1 to `10.0.0.2` and host2 to `10.0.0.3`). You can ping these private addresses to confirm that the tunnel is working. 

Currently, the client is hardcoded to assume that every peer always provides the `10.0.0.0/24` subnet (the ip range that a peer can provide is called its `allowed ips`, as seen above). This effectively means the current demo only supports one peer for each host, as only one peer can be associated with an ip range at a time. This list of allowed ips would ideally be provided by the authentication server in the future, associated with a device record.