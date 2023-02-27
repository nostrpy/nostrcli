import json
import time
import uuid

import click

from nostr.commands.config import Config
from nostr.event import EncryptedDirectMessage, Event, EventKind
from nostr.filter import Filter, Filters
from nostr.key import PrivateKey, PublicKey
from nostr.message_type import ClientMessageType
from nostr.relay_manager import RelayManager
from nostr.utils import dict2obj


@click.group()
@click.option("-c", "--config", required=False, type=str, help="Config file")
@click.pass_context
def cli(ctx, config: str = None):
    """Command related to message(s)."""
    ctx.ensure_object(dict)

    # Set default relays
    ctx.obj['relays'] = ["wss://nostr-pub.wellorder.net", "wss://relay.damus.io"]

    config = Config.load(config)
    if config:
        try:
            relays = dict2obj(config).nostr[0].relays
            if relays:
                ctx.obj['relays'] = relays
        except AttributeError:
            pass

        try:
            influencers = dict2obj(config).nostr[0].listen
            if influencers:
                ctx.obj['influencers'] = influencers
        except AttributeError:
            pass

        try:
            ctx.obj['self'] = dict2obj(config).nostr[0].self[0]
        except AttributeError:
            pass

        try:
            receivers = dict2obj(config).nostr[0].receiver
            if receivers:
                ctx.obj['receivers'] = receivers
        except AttributeError:
            pass


@cli.command()
@click.option("-i", "--identifier", required=False, type=str)
@click.option("-p", "--pub-key", "npub", required=False, type=str)
@click.option("-l", "--limit", "limit", type=int, default=10)
@click.option("-s", "--sleep", "sleep", type=int, default=2)
@click.pass_context
def receive(ctx: dict, identifier: str, npub: str, limit: int = 10, sleep: int = 2):
    """Receives messages from npub address."""
    npubs = [npub] if npub else []
    if identifier:
        for influencer in ctx.obj.get('influencers', []):
            if hasattr(influencer, identifier):
                try:
                    npubs.append(getattr(influencer, identifier).npub)
                except AttributeError:
                    pass

    if not npubs:
        print(
            "Please input `npub`; and/or",
            "specify listen `identifier` by creating the config file",
        )
        return 1

    authors = [PublicKey.from_npub(npub).hex() for npub in npubs]
    filters = Filters(
        [Filter(authors=authors, kinds=[EventKind.TEXT_NOTE], limit=limit)]
    )
    subscription_id = uuid.uuid1().hex
    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters.to_json_array())

    relay_manager = RelayManager()
    for relay in ctx.obj['relays']:
        relay_manager.add_relay(relay)
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
                {"Public key(s)": npubs, "Events": events, "Notices": notices}, indent=2
            )
        )
    return 0


@cli.command()
@click.option("-s", "--sec-key", "nsec", required=False, type=str)
@click.option("-m", "--message", "message", type=str)
@click.option("--sleep", "sleep", type=int, default=2)
@click.pass_context
def publish(ctx: dict, nsec: str, message: str, sleep: int = 2):
    """Sends a message."""
    if not nsec and ctx.obj.get('self'):
        try:
            nsec = ctx.obj.get('self').nsec
        except AttributeError:
            pass

    if not nsec:
        print(
            "Please input `nsec`; and/or",
            "set `nsec`, under `self` block in config file",
        )
        return 1
    private_key = PrivateKey.from_nsec(nsec)
    event = Event(content=message, public_key=private_key.public_key.hex())
    event.sign(private_key.hex())

    msg = json.dumps([ClientMessageType.EVENT, event.to_dict()])

    relay_manager = RelayManager()
    for relay in ctx.obj['relays']:
        relay_manager.add_relay(relay)
    with relay_manager:
        time.sleep(sleep)  # allow the connections to open
        relay_manager.publish_message(msg)

    click.echo(json.dumps({"Message": message}, indent=2))
    return 0


@cli.command()
@click.option("-s", "--sec-key", "nsec", required=False, type=str)
@click.option("-m", "--message", "message", type=str)
@click.option("-i", "--identifier", required=False, type=str)
@click.option("-p", "--pub-key", "receiver_npub", required=False, type=str)
@click.option("--sleep", "sleep", type=int, default=2)
@click.pass_context
def send(
    ctx: dict,
    nsec: str,
    message: str,
    identifier: str,
    receiver_npub: str,
    sleep: int = 2,
):
    """Sends a encryped direct message."""
    if not nsec and ctx.obj.get('self'):
        try:
            nsec = ctx.obj.get('self').nsec
        except AttributeError:
            pass

    if not nsec:
        print(
            "Please input `nsec`; and/or",
            "set `nsec`, under `self` block in config file",
        )
        return 1

    receiver_npub = receiver_npub or None
    if not receiver_npub and identifier:
        for receiver in ctx.obj.get('receivers', []):
            if hasattr(receiver, identifier):
                try:
                    receiver_npub = getattr(receiver, identifier).npub
                except AttributeError:
                    pass

    if not receiver_npub:
        print(
            "Please input `receiver_npub`; and/or",
            "specify `identifier`, which should be found",
            "under `receiver` block in config file",
        )
        return 1

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
    for relay in ctx.obj['relays']:
        relay_manager.add_relay(relay)

    with relay_manager:
        time.sleep(sleep)  # allow the connections to open
        relay_manager.publish_event(direct_message)

    click.echo(json.dumps({"Message": message}, indent=2))
    return 0
