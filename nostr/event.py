import json
import time
from dataclasses import dataclass, field
from enum import IntEnum
from hashlib import sha256
from typing import List, Optional

from .key import PrivateKey, PublicKey
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
    CHANNEL_CREATE = 40
    CHANNEL_META = 41
    CHANNEL_MESSAGE = 42
    CHANNEL_HIDE = 43
    CHANNEL_MUTE = 44
    RELAY_LIST_METADATA = 10002


@dataclass
class Event:
    """Event class.

    :param content: content string
    :param public_key: public key in hex form
    :param created_at: event creation date
    :param kind: event kind
    :param tags: list of list of strings
    :param signature: signature, will be created after signing with a private key
    """

    content: Optional[str] = None
    public_key: Optional[str] = None
    created_at: Optional[int] = None
    kind: Optional[int] = EventKind.TEXT_NOTE
    tags: List[List[str]] = field(default_factory=list)
    signature: Optional[str] = None

    def __post_init__(self) -> None:
        if self.content and not isinstance(self.content, str):
            raise TypeError("Argument 'content' must be of type str")
        # elif (
        #     self.content
        #     and "?iv" not in self.content
        #     and self.kind == EventKind.ENCRYPTED_DIRECT_MESSAGE
        # ):
        #     raise Exception(
        #         "Encrypted DMs cannot use the `content` field; use encrypt_dm()"
        #         "for storing an encrypted content."
        #     )

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

    def encrypt_dm(
        self, private_key_hex: str, cleartext_content: str, recipient_pubkey: str
    ) -> None:
        if self.kind != EventKind.ENCRYPTED_DIRECT_MESSAGE:
            raise Exception("Wrong event kind, needs to be ENCRYPTED_DIRECT_MESSAGE")
        if not self.has_pubkey_ref(recipient_pubkey):
            # Must specify the DM recipient's pubkey in a 'p' tag
            self.add_pubkey_ref(recipient_pubkey)
        sk = PrivateKey(bytes.fromhex(private_key_hex))
        encrypted_message = sk.encrypt_message(
            message=cleartext_content, public_key_hex=recipient_pubkey
        )
        self.content = encrypted_message

    def sign(self, private_key_hex: str) -> None:
        """signs the event with the private key and stored the signature in self.sig.
        The pubkey from the event is replaced and the note id recomputed.
        :param private_key_hex: private key as hex string
        """
        if self.kind == EventKind.ENCRYPTED_DIRECT_MESSAGE and self.content is None:
            raise Exception("Message is not yet encrypted!")
        sk = PrivateKey(bytes.fromhex(private_key_hex))
        self.public_key = sk.public_key.hex()
        sig = sk.sign(bytes.fromhex(self.id))
        self.signature = sig.hex()

    def add_pubkey_ref(self, pubkey: str):
        """Adds a reference to a pubkey as a 'p' tag."""
        self.tags.append(["p", pubkey])

    def has_pubkey_ref(self, pubkey: str) -> bool:
        """Check if a `p` tag to the given pubkey exists."""
        for tag_type, tag in self.tags:
            if tag_type == "p" and tag == pubkey:
                return True
        return False

    def add_event_ref(self, event_id: str):
        """Adds a reference to an event_id as an 'e' tag."""
        self.tags.append(["e", event_id])

    def has_event_ref(self, event_id: str):
        """Check if a `e` tag to the given event_id exists."""
        for tag_type, tag in self.tags:
            if tag_type == "e" and tag == event_id:
                return True
        return False

    def get_tag_dict(self):
        """Returns all tags as dict."""
        ret = {}
        tag_types = self.get_tag_types()
        for t in tag_types:
            ret[t] = self.get_tag_list(tag_type=t)
        return ret

    def get_tag_list(self, tag_type: str = "e"):
        """Returns all tags of given type as list."""
        ret = []
        for _tag_type, _tag in self.tags:
            if _tag_type == tag_type:
                ret.append(_tag)
        return ret

    def get_tag_types(self):
        """Returns list of all included tag types."""
        ret = []
        for tag_type, _ in self.tags:
            if tag_type not in ret:
                ret.append(tag_type)
        return ret

    def get_tag_count(self, tag_type: str = "e"):
        """Returns all tags of given type as list."""
        count = 0
        for _tag_type, _tag in self.tags:
            if _tag_type == tag_type:
                count += 1
        return count

    def verify(self) -> bool:
        pub_key = PublicKey.from_hex(self.public_key)
        return pub_key.verify(bytes.fromhex(self.signature), bytes.fromhex(self.id))

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

    def __repr__(self):
        note_id = self.bech32()
        return f"Event({note_id[:10]}...{note_id[-10:]})"

    def __str__(self):
        return self.to_message()


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
