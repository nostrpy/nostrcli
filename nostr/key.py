import binascii
import secrets
from base64 import b64decode, b64encode
from hashlib import sha256
from typing import Optional

import coincurve as secp256k1
from coincurve._libsecp256k1 import ffi, lib
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from . import bech32
from .delegation import Delegation

# from .event import EncryptedDirectMessage, Event, EventKind

HAS_ECDH = hasattr(lib, "secp256k1_ecdh")


class PublicKey:
    def __init__(self, raw_bytes: bytes) -> None:
        """
        :param raw_bytes: The formatted public key.
        :type data: bytes
        """
        if isinstance(raw_bytes, PrivateKey):
            self.raw_bytes = raw_bytes.public_key.raw_bytes
        elif isinstance(raw_bytes, secp256k1.keys.PublicKey):
            self.raw_bytes = raw_bytes.format(compressed=True)[2:]
        elif isinstance(raw_bytes, secp256k1.keys.PublicKeyXOnly):
            self.raw_bytes = raw_bytes.format()
        elif isinstance(raw_bytes, str):
            self.raw_bytes = binascii.unhexlify(raw_bytes)
        else:
            self.raw_bytes = raw_bytes

    def bech32(self) -> str:
        converted_bits = bech32.convertbits(self.raw_bytes, 8, 5)
        return bech32.bech32_encode("npub", converted_bits, bech32.Encoding.BECH32)

    def hex(self) -> str:
        return self.raw_bytes.hex()

    def verify_signed_message_hash(self, hash: str, sig: str) -> bool:
        pk = secp256k1.PublicKey(b"\x02" + self.raw_bytes, True)
        return pk.schnorr_verify(bytes.fromhex(hash), bytes.fromhex(sig), None, True)

    def verify(self, sig: bytes, message: bytes) -> bool:
        pk = secp256k1.PublicKeyXOnly(self.raw_bytes)
        return pk.verify(sig, message)

    @classmethod
    def from_hex(cls, hex: str) -> "PublicKey":
        return cls(bytes.fromhex(hex))

    @classmethod
    def from_npub(cls, npub: str):
        """Load a PublicKey from its bech32/npub form."""
        hrp, data, spec = bech32.bech32_decode(npub)
        raw_public_key = bech32.convertbits(data, 5, 8)[:-1]
        return cls(bytes(raw_public_key))


class PrivateKey:
    def __init__(self, raw_secret: Optional[bytes] = None) -> None:
        if raw_secret:
            self.raw_secret = raw_secret
        else:
            self.raw_secret = secrets.token_bytes(32)

        sk = secp256k1.PrivateKey(self.raw_secret)
        self.public_key = PublicKey(sk.public_key_xonly)

    @classmethod
    def from_nsec(cls, nsec: str):
        """Load a PrivateKey from its bech32/nsec form."""
        hrp, data, spec = bech32.bech32_decode(nsec)
        raw_secret = bech32.convertbits(data, 5, 8)[:-1]
        return cls(bytes(raw_secret))

    @classmethod
    def from_hex(cls, hex: str):
        """Load a PrivateKey from its hex form."""
        return cls(binascii.unhexlify(hex))

    def bech32(self) -> str:
        converted_bits = bech32.convertbits(self.raw_secret, 8, 5)
        return bech32.bech32_encode("nsec", converted_bits, bech32.Encoding.BECH32)

    def hex(self) -> str:
        return self.raw_secret.hex()

    def ecdh(self, public_key_hex):
        assert public_key_hex, "No public key defined"
        if not HAS_ECDH:
            raise Exception("secp256k1_ecdh not enabled")
        sk = secp256k1.PrivateKey(self.raw_secret)
        result = ffi.new("char [32]")
        pk = secp256k1.PublicKey(bytes.fromhex("02" + public_key_hex))
        res = lib.secp256k1_ecdh(
            sk.context.ctx, result, pk.public_key, self.raw_secret, copy_x, ffi.NULL
        )
        if not res:
            raise Exception(f"invalid scalar ({res})")

        return bytes(ffi.buffer(result, 32))

    def tweak_add(self, scalar: bytes) -> bytes:
        sk = secp256k1.PrivateKey(self.raw_secret)
        return sk.tweak_add(scalar)

    def compute_shared_secret(self, public_key_hex: str) -> bytes:
        return self.ecdh(public_key_hex)
        # pk = secp256k1.PublicKey(bytes.fromhex("02" + public_key_hex), True)
        # return pk.ecdh(self.raw_secret, hashfn=copy_x)

    def encrypt_message(self, message: str, public_key_hex: str) -> str:
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(message.encode()) + padder.finalize()

        iv = secrets.token_bytes(16)
        cipher = Cipher(
            algorithms.AES(self.compute_shared_secret(public_key_hex)), modes.CBC(iv)
        )

        encryptor = cipher.encryptor()
        encrypted_message = encryptor.update(padded_data) + encryptor.finalize()

        return f"{b64encode(encrypted_message).decode()}?iv={b64encode(iv).decode()}"

    # def encrypt_dm(self, dm: EncryptedDirectMessage) -> None:
    #     dm.content = self.encrypt_message(
    #         message=dm.cleartext_content, public_key_hex=dm.recipient_pubkey
    #     )

    def decrypt_message(self, encoded_message: str, public_key_hex: str) -> str:
        encoded_data = encoded_message.split("?iv=")
        encoded_content, encoded_iv = encoded_data[0], encoded_data[1]

        iv = b64decode(encoded_iv)
        cipher = Cipher(
            algorithms.AES(self.compute_shared_secret(public_key_hex)), modes.CBC(iv)
        )
        encrypted_content = b64decode(encoded_content)

        decryptor = cipher.decryptor()
        decrypted_message = decryptor.update(encrypted_content) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        unpadded_data = unpadder.update(decrypted_message) + unpadder.finalize()

        return unpadded_data.decode()

    def sign_message_hash(self, hash: bytes) -> str:
        sk = secp256k1.PrivateKey(self.raw_secret)
        sig = sk.schnorr_sign(hash, None, raw=True)
        return sig.hex()

    def sign(self, message: bytes, aux_randomness: bytes = b"") -> str:
        sk = secp256k1.PrivateKey(self.raw_secret)
        return sk.sign_schnorr(message, aux_randomness)

    def sign_delegation(self, delegation: Delegation) -> None:
        delegation.signature = self.sign_message_hash(
            sha256(delegation.delegation_token.encode()).digest()
        )

    def __eq__(self, other):
        return self.raw_secret == other.raw_secret


def mine_vanity_key(
    prefix: Optional[str] = None, suffix: Optional[str] = None
) -> PrivateKey:
    if prefix is None and suffix is None:
        raise ValueError("Expected at least one of 'prefix' or 'suffix' arguments")

    while True:
        sk = PrivateKey()
        if (
            prefix is not None
            and not sk.public_key.bech32()[5 : 5 + len(prefix)] == prefix
        ):
            continue
        if suffix is not None and not sk.public_key.bech32()[-len(suffix) :] == suffix:
            continue
        break

    return sk


@ffi.callback(
    "int (unsigned char *, const unsigned char *, const unsigned char *, void *)"
)
def copy_x(output, x32, y32, data):
    ffi.memmove(output, x32, 32)
    return 1
