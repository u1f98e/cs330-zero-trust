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

