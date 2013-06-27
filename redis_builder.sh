#!/bin/sh

REDIS_VERSION="2.6.14"

# Save the build dir path to a variable.
BUILD_DIR=$PWD

# Run this build in ~ so build files aren't deleted with the temp build folder.
# This is so we don't have to re-compile redis *every* time changes are pushed (that would be unnecessary).
cd ~

[ -d "redis-${REDIS_VERSION}" ] ||
{
	echo "Downloading redis";
	wget http://redis.googlecode.com/files/redis-${REDIS_VERSION}.tar.gz;
	tar xzf redis-${REDIS_VERSION}.tar.gz;
}

cd redis-${REDIS_VERSION}

echo "Building redis"
make
make test
cp src/redis-server ~/redis-server

cd ${BUILD_DIR}
cp redis.conf ~/redis.conf.in1
