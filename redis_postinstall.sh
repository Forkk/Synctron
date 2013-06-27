#!/bin/sh
echo "Setting env vars"
cd
sed -e "s|{port}|${PORT_REDIS}|" redis.conf.in1 > redis.conf.in2
sed -e "s|{password}|${REDIS_PASSWORD}|" redis.conf.in2 > redis.conf
cat redis.conf
