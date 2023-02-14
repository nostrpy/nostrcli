import json
import time
from dataclasses import dataclass, field
from enum import IntEnum
from hashlib import sha256
from typing import List, Optional

from secp256k1 import PrivateKey, PublicKey

from .message_type import ClientMessageType


class EventKind(IntEnum):
    SET_METADATA = 0
    TEXT_NOTE = 1
    RECOMMEND_RELAY = 2
    CONTACTS = 3
    ENCRYPTED_DIRECT_MESSAGE = 4
    DELETE = 5
    BOOST = 6
    REACTION = 7


@dataclass
class Event:
    content: Optional[str] = None
    public_key: Optional[str] = None
    created_at: Optional[int] = None
    kind: Optional[int] = EventKind.TEXT_NOTE
    tags: List[List[str]] = field(default_factory=list)
    signature: Optional[str] = None

    def __post_init__(self) -> None:
        if self.content and not isinstance(self.content, str):
            raise TypeError("Argument 'content' must be of type str")

        if self.created_at is None:
            self.created_at = int(time.time())

    @staticmethod
    def serialize(
        public_key: str, created_at: int, kind: int, tags: List[List[str]], content: str
    ) -> bytes:
        data = [0, public_key, created_at, kind, tags, content]
        data_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        return data_str.encode()

    @staticmethod
    def compute_id(
        public_key: str, created_at: int, kind: int, tags: List[List[str]], content: str
    ):
        return sha256(
            Event.serialize(public_key, created_at, kind, tags, content)
        ).hexdigest()

    @property
    def id(self) -> str:
        # Always recompute the id to reflect the up-to-date state of the Event
        return Event.compute_id(
            self.public_key, self.created_at, self.kind, self.tags, self.content
        )

    def sign(self, private_key_hex: str) -> None:
        sk = PrivateKey(bytes.fromhex(private_key_hex))
        sig = sk.schnorr_sign(bytes.fromhex(self.id), None, raw=True)
        self.signature = sig.hex()

    def add_pubkey_ref(self, pubkey: str):
        """Adds a reference to a pubkey as a 'p' tag."""
        self.tags.append(["p", pubkey])

    def add_event_ref(self, event_id: str):
        """Adds a reference to an event_id as an 'e' tag."""
        self.tags.append(["e", event_id])

    def verify(self) -> bool:
        pub_key = PublicKey(
            bytes.fromhex("02" + self.public_key), True
        )  # add 02 for schnorr (bip340)
        event_id = Event.compute_id(
            self.public_key, self.created_at, self.kind, self.tags, self.content
        )
        return pub_key.schnorr_verify(
            bytes.fromhex(event_id), bytes.fromhex(self.signature), None, raw=True
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pubkey": self.public_key,
            "created_at": self.created_at,
            "kind": self.kind,
            "tags": self.tags,
            "content": self.content,
            "sig": self.signature,
        }

    @classmethod
    def from_dict(cls, msg: dict) -> "Event":
        return Event(
            content=msg["content"],
            public_key=msg["pubkey"],
            created_at=msg["created_at"],
            kind=msg["kind"],
            tags=msg["tags"],
            signature=msg["sig"],
        )

    def to_message(self) -> str:
        return json.dumps([ClientMessageType.EVENT, self.to_dict()])


@dataclass
class EncryptedDirectMessage(Event):
    recipient_pubkey: str = None
    cleartext_content: str = None
    reference_event_id: str = None

    def __post_init__(self):
        if self.content:
            self.cleartext_content = self.content
            self.content = None

        if self.recipient_pubkey is None:
            raise Exception("Must specify a recipient_pubkey.")

        self.kind = EventKind.ENCRYPTED_DIRECT_MESSAGE
        super().__post_init__()

        # Must specify the DM recipient's pubkey in a 'p' tag
        self.add_pubkey_ref(self.recipient_pubkey)

        # Optionally specify a reference event (DM) this is a reply to
        if self.reference_event_id:
            self.add_event_ref(self.reference_event_id)

    @property
    def id(self) -> str:
        if self.content is None:
            raise Exception(
                "EncryptedDirectMessage `id` is undefined \
                until its message is encrypted and stored in the `content` field"
            )
        return super().id
