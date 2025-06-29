# -*- coding: utf-8 -*-

import base64
import os

from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA


def get_public_key() -> RSA.RsaKey:
    public_key_path = os.path.join(
        os.path.dirname(__file__),
        "keys/public.pem",
    )
    with open(public_key_path, "rb") as f:
        pub_key = RSA.importKey(f.read())
    return pub_key


def get_private_key() -> RSA.RsaKey:
    private_key_path = os.path.join(
        os.path.dirname(__file__),
        "keys/private.pem",
    )
    with open(private_key_path, "rb") as f:
        pri_key = RSA.importKey(f.read())
    return pri_key


public_key = get_public_key()
private_key = get_private_key()


def encrypt_with_rsa(content: str) -> str:
    """
    Encrypt a message using RSA public key

    Args:
        content: The content to be encrypted

    Returns:
        Base64 encoded encrypted message as string
    """
    # Create cipher
    cipher = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)

    # Encrypt message and convert to base64 string
    encrypted_bytes = cipher.encrypt(content.encode())
    return base64.b64encode(encrypted_bytes).decode("utf-8")


def decrypt_with_rsa(content: str) -> str:
    """
    Decrypt a message using RSA public key

    Args:
        content: The content to be decrypted

    Returns:
        Base64 decoded encrypted message as string
    """
    # Create cipher
    cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)

    # Decrypt content
    encrypted_bytes = base64.b64decode(content)
    decrypted_bytes = cipher.decrypt(encrypted_bytes)
    return decrypted_bytes.decode("utf-8")


def mask_string(input_str: str) -> str:
    """
    1. if content length is less than 12, return 32x*
    2. if content length is more than 12，keep first and last 4 chars,
    rest chars will be replaced with *

    Args:
        input_str: input string

    Returns:
        Processed string
    """
    if len(input_str) <= 12:
        return "*" * 32

    prefix = input_str[:4]
    suffix = input_str[-4:]

    middle_length = len(input_str) - 8
    middle = "*" * middle_length

    return prefix + middle + suffix
