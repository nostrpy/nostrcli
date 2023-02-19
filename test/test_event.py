import time
import unittest
from unittest.mock import ANY

import pytest

from nostr.event import EncryptedDirectMessage, Event, EventKind
from nostr.key import PrivateKey


class TestEvent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sender_pk = PrivateKey()
        cls.sender_pubkey = cls.sender_pk.public_key.hex()

    def test_note_event(self):
        pk1 = PrivateKey.from_hex(
            "964b29795d621cdacf05fd94fb23206c88742db1fa50b34d7545f3a2221d8124"
        )
        event = Event("Hello Nostr!", pk1.public_key.hex())
        event.created_at = 1671406583
        event.sign(pk1.hex())
        self.assertEqual(
            "23411895658d374ec922adf774a70172290b2c738ae67815bd8945e5d8fff3bb", event.id
        )
        self.assertTrue(event.verify())

    def test_event_default_time(self):
        """
        Ensure created_at default value reflects the time at Event object instantiation
        see: https://github.com/jeffthibault/python-nostr/issues/23
        """
        event1 = Event(content="test event")
        time.sleep(1.5)
        event2 = Event(content="test event")
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
        self.assertTrue(["e", some_event_id] in event.tags)
        self.assertEqual(event.get_tag_count("e"), 1)
        self.assertEqual(event.get_tag_count("p"), 0)
        self.assertEqual(event.get_tag_list("e"), [some_event_id])
        self.assertEqual(event.get_tag_list("p"), [])
        self.assertEqual(event.get_tag_types(), ["e"])
        self.assertEqual(event.get_tag_dict(), {"e": [some_event_id]})
        self.assertTrue(event.has_event_ref(some_event_id))

    def test_add_pubkey_ref(self):
        """Should add a 'p' tag for each pubkey_ref added."""
        some_pubkey = "some_pubkey"
        event = Event(content="Adding a 'p' tag")
        event.add_pubkey_ref(some_pubkey)
        self.assertTrue(["p", some_pubkey] in event.tags)
        self.assertEqual(event.get_tag_count("p"), 1)
        self.assertEqual(event.get_tag_count("e"), 0)
        self.assertEqual(event.get_tag_list("p"), [some_pubkey])
        self.assertEqual(event.get_tag_list("e"), [])
        self.assertEqual(event.get_tag_types(), ["p"])
        self.assertEqual(event.get_tag_dict(), {"p": [some_pubkey]})
        self.assertTrue(event.has_pubkey_ref(some_pubkey))

    def test_sign_event_is_valid(self):
        """Sign should create a signature that can be verified against Event.id."""
        event = Event(content="Hello, world!")
        event.sign(self.sender_pk.hex())
        self.assertTrue(event.verify())

    def test_sign_event_adds_pubkey(self):
        """Sign should add the sender's pubkey if not already specified."""
        event = Event(content="Hello, world!")

        # The event's public_key hasn't been specified yet
        self.assertTrue(event.public_key is None)
        event.sign(self.sender_pk.hex())

        # PrivateKey.sign() should have populated public_key
        self.assertEqual(event.public_key, self.sender_pubkey)

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

    def test_decrypt_event(self):
        dm1 = Event.from_dict(
            {
                "id": "46c76ec67d03babdb840254b3667585143cc499497b0a6a40aedc9ce2de416"
                "70",
                "pubkey": "f3c25355c29f64ea8e9b4e11b583ac0a7d0d8235f156cffec2b73e5756a"
                "ab206",
                "created_at": 1674819397,
                "kind": 4,
                "tags": [
                    [
                        "p",
                        "a1db8e8b047e1350958a55e0a853151d0e1f685fa5cf3772e01bccc5aa5c"
                        "b2eb",
                    ]
                ],
                "content": "VOqWLiW4wv8+fDsNC00a1w==?iv=LSIH1sk13Mw09PV8Z80sag==",
                "sig": "982e825d32e78bf695a2511e14d2958e0d480bfa338e12307e5eb7ecad3b"
                "d86d53c2d508df9083a0fc25b44c44ae4c622f7405bbc2ca723c5dbc98da48214f16",
            }
        )
        self.assertTrue(dm1.verify())


class TestEncryptedDirectMessage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sender_pk = PrivateKey.from_hex(
            "29307c4354b7d9d311d2cec4878c0de56c93a921d300273c19577e9004de3c9f"
        )
        cls.sender_pubkey = cls.sender_pk.public_key.hex()
        cls.recipient_pk = PrivateKey.from_hex(
            "4138d1b6dde34f81c38cef2630429e85847dd5b70508e37f53c844f66f19f983"
        )
        cls.recipient_pubkey = cls.recipient_pk.public_key.hex()

    def test_content_field_moved_to_cleartext_content(self):
        """Should transfer `content` field data to `cleartext_content`"""
        dm = EncryptedDirectMessage(
            content="My message!", recipient_pubkey=self.recipient_pubkey
        )
        self.assertEqual(dm.content, None)
        self.assertNotEqual(dm.cleartext_content, None)

    def test_nokwarg_content_allowed(self):
        """Should allow creating a new DM w/no `content` nor `cleartext_content`
        kwarg."""
        dm = EncryptedDirectMessage(
            "My message!", recipient_pubkey=self.recipient_pubkey
        )
        assert dm.cleartext_content is not None

    # def test_content_field_not_allowed(self):
    #     """Should not let users instantiate a new DM with `content` field data."""
    #     with self.assertRaisesRegex(Exception, "cannot use"):
    #         Event(content="My message!", kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)

    def test_recipient_p_tag(self):
        """Should generate recipient 'p' tag."""
        dm = EncryptedDirectMessage(
            cleartext_content="Secret message!", recipient_pubkey=self.recipient_pubkey
        )
        assert ["p", self.recipient_pubkey] in dm.tags

    def test_unencrypted_dm_has_undefined_id(self):
        """Should raise Exception if `id` is requested before DM is encrypted."""
        dm = EncryptedDirectMessage(
            cleartext_content="My message!", recipient_pubkey=self.recipient_pubkey
        )

        with pytest.raises(Exception) as e:
            dm.id
        assert "undefined" in str(e)

        # But once we encrypt it, we can request its id
        # self.sender_pk.encrypt_dm(dm)
        dm.encrypt_dm(
            self.sender_pk.hex(),
            cleartext_content="My message!",
            recipient_pubkey=self.recipient_pubkey,
        )
        assert dm.id is not None

    def test_encrypt_dm(self):
        """Should encrypt a DM and populate its `content` field with ciphertext that
        either party can decrypt."""
        message = "My secret message!"

        dm = EncryptedDirectMessage(
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content=message,
        )

        # DM's content field should be initially blank
        assert dm.content is None
        dm.encrypt_dm(
            self.sender_pk.hex(),
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content=message,
        )

        # After encrypting, the content field should now be populated
        assert dm.content is not None

        # Sender should be able to decrypt
        decrypted_message = self.sender_pk.decrypt_message(
            encoded_message=dm.content, public_key_hex=self.recipient_pubkey
        )
        assert decrypted_message == message

        # Recipient should be able to decrypt by referencing the sender's pubkey
        decrypted_message = self.recipient_pk.decrypt_message(
            encoded_message=dm.content, public_key_hex=self.sender_pubkey
        )
        assert decrypted_message == message

    def test_encrypt_dm_2(self):
        """Should encrypt a DM and populate its `content` field with ciphertext that
        either party can decrypt."""
        message1 = "Test"
        message2 = "Test2"
        message3 = "Test3"
        message4 = "Test4"

        dm1 = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
        self.assertTrue(dm1.content is None)
        dm1.encrypt_dm(
            self.sender_pk.hex(),
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content=message1,
        )
        dm2 = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
        dm2.encrypt_dm(
            self.recipient_pk.hex(),
            recipient_pubkey=self.sender_pubkey,
            cleartext_content=message2,
        )
        dm3 = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
        dm3.encrypt_dm(
            self.sender_pk.hex(),
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content=message3,
        )
        dm4 = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
        dm4.encrypt_dm(
            self.recipient_pk.hex(),
            recipient_pubkey=self.sender_pubkey,
            cleartext_content=message4,
        )

        # After encrypting, the content field should now be populated
        self.assertTrue(dm1.content is not None)

        # Sender should be able to decrypt
        decm1_sender = self.sender_pk.decrypt_message(
            encoded_message=dm1.content, public_key_hex=self.recipient_pubkey
        )
        decm2_sender = self.sender_pk.decrypt_message(
            encoded_message=dm2.content, public_key_hex=self.recipient_pubkey
        )
        decm3_sender = self.sender_pk.decrypt_message(
            encoded_message=dm3.content, public_key_hex=self.recipient_pubkey
        )
        decm4_sender = self.sender_pk.decrypt_message(
            encoded_message=dm4.content, public_key_hex=self.recipient_pubkey
        )

        decm1_receiver = self.recipient_pk.decrypt_message(
            encoded_message=dm1.content, public_key_hex=self.sender_pubkey
        )
        decm2_receiver = self.recipient_pk.decrypt_message(
            encoded_message=dm2.content, public_key_hex=self.sender_pubkey
        )
        decm3_receiver = self.recipient_pk.decrypt_message(
            encoded_message=dm3.content, public_key_hex=self.sender_pubkey
        )
        decm4_receiver = self.recipient_pk.decrypt_message(
            encoded_message=dm4.content, public_key_hex=self.sender_pubkey
        )
        self.assertEqual(message1, decm1_receiver)
        self.assertEqual(message1, decm1_sender)
        self.assertEqual(message2, decm2_receiver)
        self.assertEqual(message2, decm2_sender)
        self.assertEqual(message3, decm3_receiver)
        self.assertEqual(message3, decm3_sender)
        self.assertEqual(message4, decm4_receiver)
        self.assertEqual(message4, decm4_sender)

    def test_decrypt_dm(self):
        message1 = "Test"
        message2 = "Test2"
        message3 = "Test3"
        message4 = "Test4"
        encrypt1 = "VOqWLiW4wv8+fDsNC00a1w==?iv=LSIH1sk13Mw09PV8Z80sag=="
        encrypt2 = "abZBRLPta8888xDkg6pUWA==?iv=Gj5KOUbFqREhSdbMENRKEg=="
        encrypt3 = "w2AsXNN0EysjG6/E/GZWPg==?iv=3c7qsPxSOckGeqjjpwQQ4A=="
        encrypt4 = "nBfP5P2GEEOlfNYMoxADDg==?iv=VsFd7eE8BfoyDJpfQ7kjhQ=="

        dm_s1 = self.sender_pk.decrypt_message(
            encoded_message=encrypt1, public_key_hex=self.recipient_pubkey
        )
        dm_s2 = self.sender_pk.decrypt_message(
            encoded_message=encrypt2, public_key_hex=self.recipient_pubkey
        )
        dm_s3 = self.sender_pk.decrypt_message(
            encoded_message=encrypt3, public_key_hex=self.recipient_pubkey
        )
        dm_s4 = self.sender_pk.decrypt_message(
            encoded_message=encrypt4, public_key_hex=self.recipient_pubkey
        )
        self.assertEqual(dm_s1, message1)
        self.assertEqual(dm_s2, message2)
        self.assertEqual(dm_s3, message3)
        self.assertEqual(dm_s4, message4)

        dm_r1 = self.recipient_pk.decrypt_message(
            encoded_message=encrypt1, public_key_hex=self.sender_pubkey
        )
        dm_r2 = self.recipient_pk.decrypt_message(
            encoded_message=encrypt2, public_key_hex=self.sender_pubkey
        )
        dm_r3 = self.recipient_pk.decrypt_message(
            encoded_message=encrypt3, public_key_hex=self.sender_pubkey
        )
        dm_r4 = self.recipient_pk.decrypt_message(
            encoded_message=encrypt4, public_key_hex=self.sender_pubkey
        )
        self.assertEqual(dm_r1, message1)
        self.assertEqual(dm_r2, message2)
        self.assertEqual(dm_r3, message3)
        self.assertEqual(dm_r4, message4)

    def test_sign_encrypts_dm(self):
        """`sign` should encrypt a DM that hasn't been encrypted yet."""
        dm = Event(kind=EventKind.ENCRYPTED_DIRECT_MESSAGE)
        self.assertTrue(dm.content is None)
        dm.encrypt_dm(
            self.sender_pk.hex(),
            recipient_pubkey=self.recipient_pubkey,
            cleartext_content="Some DM message",
        )

        dm.sign(self.sender_pk.hex())

        self.assertTrue(dm.content is not None)
