import unittest

from nostr.event import Event
from nostr.key import PrivateKey
from nostr.relay_manager import RelayException, RelayManager

# def test_only_relay_valid_events():
#     """Publish_event raise a RelayException if an Event fails verification."""
#     pk = PrivateKey()
#     event = Event(
#         public_key=pk.public_key.hex(),
#         content="Hello, world!",
#     )

#     relay_manager = RelayManager()

#     # Deliberately forget to sign the Event
#     with pytest.raises(RelayException) as e:
#         relay_manager.publish_event(event)
#     assert "must be signed" in str(e)

#     # Attempt to relay with a nonsense signature
#     event.signature = "0" * 32
#     with pytest.raises(RelayException) as e:
#         relay_manager.publish_event(event)
#     assert "failed to verify" in str(e)

#     # Properly signed Event can be relayed
#     pk.sign_event(event)
#     relay_manager.publish_event(event)


class TestPrivateKey(unittest.TestCase):
    def test_only_relay_valid_events(self):
        """publish_event raise a RelayException if an Event fails verification."""
        pk = PrivateKey()
        event = Event(
            public_key=pk.public_key.hex(),
            content="Hello, world!",
        )

        relay_manager = RelayManager()

        # Deliberately forget to sign the Event
        with self.assertRaisesRegex(RelayException, "must be signed"):
            relay_manager.publish_event(event)

        # Attempt to relay with a nonsense signature
        event.signature = (b"\00" * 64).hex()
        with self.assertRaisesRegex(RelayException, "failed to verify"):
            relay_manager.publish_event(event)

        # Properly signed Event can be relayed
        event.sign(pk.hex())
        relay_manager.publish_event(event)
