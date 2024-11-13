# zt-clientd
A client daemon that runs in the background, automatically validating connection requests and creating wireguard tunnels.

## Installation
```bash
# If you haven't cloned submodules, get them
git submodule update --init

# Configure the build 
cmake -B build -S .
# Build the project
cmake --build build

# Install the project to the system
cmake --install build
```

After installation, you can start and enable the service:
```bash
sudo systemctl daemon-reload # Done once after installation
sudo systemctl enable zt-client.service # Enable on startup (optional)
sudo systemctl start zt-client.service
```

## License
wireguard.c and wireguard.h are licensed under the LGPL-2.1+.

The original source for wireguard.c and wireguard.h can be found [here](https://git.zx2c4.com/wireguard-tools/tree/contrib/embeddable-wg-library)