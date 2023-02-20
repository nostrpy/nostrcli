import json
import time
import uuid

import click

from nostr.event import EncryptedDirectMessage, Event, EventKind
from nostr.filter import Filter, Filters
from nostr.key import PrivateKey, PublicKey
from nostr.message_type import ClientMessageType
from nostr.relay_manager import RelayManager


@click.group()
def cli():
    """Command related to message(s)."""


@cli.command()
@click.option("-p", "--pub-key", "npub", required=True, type=str)
@click.option("-l", "--limit", "limit", type=int, default=10)
@click.option("--sleep", "sleep", type=int, default=2)
def receive(npub: str, limit: int = 10, sleep: int = 2):
    """Receives messages from npub address."""
    author = PublicKey.from_npub(npub)
    filters = Filters(
        [Filter(authors=[author.hex()], kinds=[EventKind.TEXT_NOTE], limit=limit)]
    )
    subscription_id = uuid.uuid1().hex
    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters.to_json_array())

    relay_manager = RelayManager()
    relay_manager.add_relay("wss://nostr-pub.wellorder.net")
    relay_manager.add_relay("wss://relay.damus.io")
    relay_manager.add_subscription(subscription_id, filters)

    def get_events(relay_manager):
        events = []
        while relay_manager.message_pool.has_events():
            event_msg = relay_manager.message_pool.get_event()
            events.append(event_msg.event.content)
        return events

    def get_notices(relay_manager):
        notices = []
        while relay_manager.message_pool.has_notices():
            notice_msg = relay_manager.message_pool.get_notice()
            notices.append(notice_msg.content)
        return notices

    with relay_manager:
        time.sleep(sleep)  # allow the connections to open
        message = json.dumps(request)
        relay_manager.publish_message(message)
        time.sleep(sleep)  # allow the messages to send

        events = get_events(relay_manager=relay_manager)
        notices = get_notices(relay_manager=relay_manager)
        click.echo(
            json.dumps(
                {"Public key": npub, "Events": events, "Notices": notices}, indent=2
            )
        )


@cli.command()
@click.option("-s", "--sec-key", "nsec", required=True, type=str)
@click.option("-m", "--message", "message", type=str)
@click.option("--sleep", "sleep", type=int, default=2)
def publish(nsec: str, message: str, sleep: int = 2):
    """Sends a message."""
    private_key = PrivateKey.from_nsec(nsec)
    event = Event(content=message, public_key=private_key.public_key.hex())
    event.sign(private_key.hex())

    msg = json.dumps([ClientMessageType.EVENT, event.to_dict()])

    relay_manager = RelayManager()
    relay_manager.add_relay("wss://nostr-pub.wellorder.net")
    relay_manager.add_relay("wss://relay.damus.io")
    with relay_manager:
        time.sleep(sleep)  # allow the connections to open
        relay_manager.publish_message(msg)

    click.echo(json.dumps({"Message": message}, indent=2))


@cli.command()
@click.option("-s", "--sec-key", "nsec", required=True, type=str)
@click.option("-m", "--message", "message", type=str)
@click.option("-p", "--pub-key", "receiver_npub", required=True, type=str)
@click.option("--sleep", "sleep", type=int, default=2)
def send(nsec: str, message: str, receiver_npub: str, sleep: int = 2):
    """Sends a encryped direct message."""
    private_key = PrivateKey.from_nsec(nsec)
    recipient_pubkey = PublicKey.from_npub(receiver_npub)
    direct_message = EncryptedDirectMessage(
        recipient_pubkey=recipient_pubkey.hex(), cleartext_content=message
    )
    direct_message.encrypt_dm(
        private_key_hex=private_key.hex(),
        cleartext_content=message,
        recipient_pubkey=recipient_pubkey.hex(),
    )
    direct_message.sign(private_key.hex())

    relay_manager = RelayManager()
    relay_manager.add_relay("wss://nostr-pub.wellorder.net")
    relay_manager.add_relay("wss://relay.damus.io")

    with relay_manager:
        time.sleep(sleep)  # allow the connections to open
        relay_manager.publish_event(direct_message)

    click.echo(json.dumps({"Message": message}, indent=2))
