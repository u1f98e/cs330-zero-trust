FROM docker.io/ubuntu:24.04

RUN DEBIAN_FRONTEND=noninteractive apt update && \
	DEBIAN_FRONTEND=noninteractive apt install -y supervisor postgresql default-jdk iproute2 net-tools wget vim nano

# Download and set up keycloak
WORKDIR /opt
RUN wget -O keycloak.tar.gz https://github.com/keycloak/keycloak/releases/download/26.0.5/keycloak-26.0.5.tar.gz &&\
	mkdir keycloak &&\
	tar -xzvf keycloak.tar.gz -C keycloak --strip-components=1 &&\
	rm keycloak.tar.gz
WORKDIR /opt/keycloak
RUN groupadd keycloak &&\
	useradd -r -g keycloak -d /opt/keycloak keycloak &&\
	chown -R keycloak:keycloak /opt/keycloak &&\
	chmod o+x /opt/keycloak/bin
WORKDIR /

# Set up postgres database
ENV POSTGRES_DB=keycloakdb \
    POSTGRES_PASSWORD=password \
    PGDATA=/var/db \
    PGADMIN_DEFAULT_EMAIL=admin@example.com \
    PGADMIN_DEFAULT_PASSWORD=password \
    PGADMIN_DISABLE_POSTFIX=true \
    PGADMIN_SERVER_JSON_FILE=/var/pgadmin-config/servers.json

RUN mkdir /var/db && chown -R postgres:postgres /var/db
USER postgres
RUN /usr/lib/postgresql/16/bin/initdb
USER root

# Set up environment for keycloak
ENV KC_BOOTSTRAP_ADMIN_USERNAME=admin \
    KC_BOOTSTRAP_ADMIN_PASSWORD=password \
    KC_CACHE=ispn \
    KC_DB=postgres \
    KC_DB_URL=jdbc:postgresql://localhost:5432/keycloakdb \
    KC_DB_USERNAME=postgres \
    KC_DB_PASSWORD=password \
    KC_LOG_LEVEL=INFO,org.infinispan:INFO,org.jgroups:INFO

# Extra scripts to set up database
COPY --chmod=755 init_db.sh /usr/bin/init_db.sh
COPY --chmod=755 start_keycloak.sh /usr/bin/start_keycloak.sh

# Copy config for supervisor, which will start our processes
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord"]
