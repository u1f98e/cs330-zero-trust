#include <memory>
#include <string>

extern "C" {
#include "wireguard.h"
}

class WgDevice {
public:
	static std::unique_ptr<WgDevice> create_device(const char* name) {
		wg_add_device(name);
		return get_device(name);
	}

	static std::unique_ptr<WgDevice> get_device(const char* name) {
		wg_device* dev;
		wg_get_device(&dev, name);
		return std::unique_ptr<WgDevice>(new WgDevice(dev));
	}

	~WgDevice() {
		wg_del_device(this->device_name.c_str());
		wg_free_device(this->dev);
	}

private:
	WgDevice(wg_device* d) {
		dev = d;
		device_name = std::string(dev->name);
	}

	std::string device_name;
	wg_device* dev;
};