# Zero Trust Experiment

# Setup

## Authentication Servers

For our authentication server, we use [Keycloak](https://keycloak.org). 

To start a keycloak instance, you can use the provided [docker compose](https://docs.docker.com/compose/install/)
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

