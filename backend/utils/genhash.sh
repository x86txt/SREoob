#!/bin/bash

# Generate a random 32-byte (64 characters hex) API key
API_KEY=$(openssl rand -hex 32)

# Generate a random 16-byte (32 characters hex) salt
SALT=$(openssl rand -hex 16)

# Hash the API key using the generated salt.
# The argon2 CLI reads the key from stdin.
# The "-e" flag ensures the output is in the standard encoded format ($argon2id$v=19$m=...$salt$hash)
# which is required by the backend verifier.
API_KEY_HASH=$(echo -n "$API_KEY" | argon2 "$SALT" -e)

# --- Display Results ---
echo -e "\n\n🎉 Your new API key and hash have been generated!"
echo "========================================"
echo "🔑 API Key (save this somewhere safe):"
echo "$API_KEY"
echo "----------------------------------------"
echo "🔒 Argon2 Hash (add this to your .env file):"
echo "$API_KEY_HASH"
echo "========================================"
echo -e "\nACTION REQUIRED:"
echo "1. Copy the API Key to your password manager."
echo "2. Copy the Argon2 Hash and add it to your .env file as:"
echo "ADMIN_API_KEY_HASH=\"$API_KEY_HASH\""
echo -e "\n"
