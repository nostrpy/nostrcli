import time
import unittest
from unittest.mock import ANY

import pytest

from nostr.event import EncryptedDirectMessage, Event
from nostr.key import PrivateKey


class TestEvent(unittest.TestCase):
    def test_event_default_time(self):
        """
        Ensure created_at default value reflects the time at Event object instantiation
        see: https://github.com/jeffthibault/python-nostr/issues/23
        """
        event1 = Event(content='test event')
        time.sleep(1.5)
        event2 = Event(content='test event')
        assert event1.created_at < event2.created_at

    def test_content_only_instantiation(self):
        """Should be able to create an Event by only specifying content without
        kwarg."""
        event = Event("Hello, world!")
        assert event.content is not None

    def test_event_id_recomputes(self):
        """Should recompute the Event.id to reflect the current Event attrs."""
        event = Event(content="some event")

        # id should be computed on the fly
        event_id = event.id

        event.created_at += 10

        # Recomputed id should now be different
        assert event.id != event_id

    def test_add_event_ref(self):
        """Should add an 'e' tag for each event_ref added."""
        some_event_id = "some_event_id"
        event = Event(content="Adding an 'e' tag")
        event.add_event_ref(some_event_id)
        assert ['e', some_event_id] in event.tags

    def test_add_pubkey_ref(self):
        """Should add a 'p' tag for each pubkey_ref added."""
        some_pubkey = "some_pubkey"
        event = Event(content="Adding a 'p' tag")
        event.add_pubkey_ref(some_pubkey)
        assert ['p', some_pubkey] in event.tags

    def test_dict_roundtrip(self):
        """Conversion to dict and back result in same object."""
        expected = {
            "content": "test event",
            "pubkey": "pubkey_any",
            "created_at": 12345678,
            "kind": 1,
            "tags": [],
            "sig": "signature",
        }
        event = Event.from_dict(expected)
        actual = event.to_dict()
        self.assertEqual(actual, {**expected, **{"id": ANY}})


class TestEncryptedDirectMessage:
    def setup_class(self):
        self.sender_pk = PrivateKey()
        self.sender_pubkey = self.sender_pk.public_key.hex()
        self.recipient_pk = PrivateKey()
        self.recipient_pubkey = self.recipient_pk.public_key.hex()

    def test_content_field_moved_to_cleartext_content(self):
        """Should transfer `content` field data to `cleartext_content`"""
        dm = EncryptedDirectMessage(
            content="My message!", recipient_pubkey=self.recipient_pubkey
        )
        assert dm.content is None
        assert dm.cleartext_content is not None

    def test_nokwarg_content_allowed(self):
        """Should allow creating a new DM w/no `content` nor `cleartext_content`
        kwarg."""
        dm = EncryptedDirectMessage(
            "My message!", recipient_pubkey=self.recipient_pubkey
        )
        assert dm.cleartext_content is not None

    def test_recipient_p_tag(self):
        """Should generate recipient 'p' tag."""
        dm = EncryptedDirectMessage(
            cleartext_content="Secret message!", recipient_pubkey=self.recipient_pubkey
        )
        assert ['p', self.recipient_pubkey] in dm.tags

    def test_unencrypted_dm_has_undefined_id(self):
        """Should raise Exception if `id` is requested before DM is encrypted."""
        dm = EncryptedDirectMessage(
            cleartext_content="My message!", recipient_pubkey=self.recipient_pubkey
        )

        with pytest.raises(Exception) as e:
            dm.id
        assert "undefined" in str(e)

        # But once we encrypt it, we can request its id
        self.sender_pk.encrypt_dm(dm)
        assert dm.id is not None
