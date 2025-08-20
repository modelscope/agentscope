#!/bin/bash

PUBLIC_KEY_FILE="app/utils/keys/public.pem"
PRIVATE_KEY_FILE="app/utils/keys/private.pem"

if [ -f "$PUBLIC_KEY_FILE" ] && [ -f "$PRIVATE_KEY_FILE" ]; then
    echo "Keys already exist. No new keys generated."
    exit 0
fi

mkdir -p $(dirname "$PUBLIC_KEY_FILE")

openssl genpkey -algorithm RSA -out "$PRIVATE_KEY_FILE" -pkeyopt rsa_keygen_bits:2048

openssl rsa -pubout -in "$PRIVATE_KEY_FILE" -out "$PUBLIC_KEY_FILE"

echo "Keys generated and saved."