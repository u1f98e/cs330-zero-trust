.PHONY: clean install uninstall

CFLAGS = -g
LDFLAGS =
BUILD_DIR ?= build
OBJ_DIR = $(BUILD_DIR)/obj

INSTALL_PREFIX ?= /
INSTALL_BIN_DIR ?= usr/local/bin

zt-clientd: $(OBJ_DIR)/main.o $(OBJ_DIR)/wireguard.o | $(BUILD_DIR)
	g++ $(LDFLAGS) $^ -o $(BUILD_DIR)/$@

$(OBJ_DIR)/main.o: main.cpp wireguard.h | $(OBJ_DIR)
	g++ -c $(CFLAGS) $< -o $@

$(OBJ_DIR)/wireguard.o: wireguard.c wireguard.h | $(OBJ_DIR)
	gcc -c $(CFLAGS) $< -o $@


$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

clean:
	rm $(BUILD_DIR)/*.o
	rm $(BUILD_DIR)/client

install: zt-clientd
	install -D $(BUILD_DIR)/zt-clientd $(INSTALL_PREFIX)/$(INSTALL_BIN_DIR)/zt-clientd
	install -m 644 -D zt-client.service $(INSTALL_PREFIX)/usr/lib/systemd/system/zt-client.service

uninstall:
	rm $(INSTALL_PREFIX)/$(INSTALL_BIN_DIR)/zt-clientd
	rm $(INSTALL_PREFIX)/usr/lib/systemd/system/zt-client.service