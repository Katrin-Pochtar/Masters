#!/bin/bash

# Generate private key and certificate for webhook
openssl req -newkey rsa:2048 -sha256 -nodes -keyout webhook_pkey.pem -x509 -days 365 -out webhook_cert.pem -subj "/C=US/ST=New York/L=New York/O=Bot/CN=51.250.111.135" 