#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include "wireguard.h"

#define MAX_JWT_SIZE 4096

template<typename _Byte_T = char>
class Serde {
public:
	typedef _Byte_T Byte_T;
	virtual ~Serde() = 0;

	virtual std::vector<Byte_T> Serialize() const = 0;
	virtual void Deserialize(std::vector<Byte_T> const& data) = 0;
};

struct PeerRequest : public Serde<> {
	virtual ~PeerRequest() {};

	wg_key requester_public_key;
	std::string auth_token;	

	virtual std::vector<Byte_T> Serialize() const override;
	virtual void Deserialize(std::vector<Byte_T> const& data) override;

	static const size_t MAX_SIZE = sizeof(wg_key) + MAX_JWT_SIZE;
};

struct PeerRequestToken : public Serde<> {


	virtual std::vector<Byte_T> Serialize() const override;
	virtual void Deserialize(std::vector<Byte_T> const& data) override;
};