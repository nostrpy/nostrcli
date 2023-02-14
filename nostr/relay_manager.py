import json
import ssl
import threading
from dataclasses import dataclass
from threading import Lock

from .event import Event
from .filter import Filters
from .message_pool import MessagePool
from .relay import Relay, RelayPolicy, RelayProxyConnectionConfig
from .request import Request


class RelayException(Exception):
    pass


@dataclass
class RelayManager:
    def __post_init__(self):
        self.relays: dict[str, Relay] = {}
        self.message_pool: MessagePool = MessagePool()
        self.lock: Lock = Lock()

    def add_relay(
        self,
        url: str,
        policy: RelayPolicy = RelayPolicy(),
        ssl_options: dict = None,
        proxy_config: RelayProxyConnectionConfig = None,
    ):
        relay = Relay(url, policy, self.message_pool)

        with self.lock:
            self.relays[url] = relay

    def remove_relay(self, url: str):
        with self.lock:
            if url in self.relays:
                relay = self.relays.pop(url)
                relay.close()

    def add_subscription(self, id: str, filters: Filters):
        with self.lock:
            for relay in self.relays.values():
                if relay.policy.should_read:
                    relay.add_subscription(id, filters)

    def close_subscription(self):
        for relay in self.relays.values():
            relay.close_subscription(id)

    def __enter__(self):
        # NOTE: This disables ssl certificate verification
        self.open_connections({"cert_reqs": ssl.CERT_NONE})

    def open_connections(self, ssl_options: dict = None):
        for relay in self.relays.values():
            threading.Thread(target=relay.connect, name=f"{relay.url}-thread").start()

    def __exit__(self, type, value, traceback):
        self.close_connections()

    def close_connections(self):
        for relay in self.relays.values():
            relay.close()

    def publish_message(self, message: str):
        for relay in self.relays.values():
            if relay.policy.should_write:
                relay.publish(message)

    def get_connection_status(self):
        out = []
        for relay in self.relays.values():
            out.append([relay.url, relay.active])
        return out

    def add_subscription_on_relay(self, url: str, id: str, filters: Filters):
        with self.lock:
            if url in self.relays:
                relay = self.relays[url]
                if not relay.policy.should_read:
                    raise RelayException(
                        f"Could not send request: {relay.url} \
                        is not configured to read from"
                    )
                relay.add_subscription(id, filters)
                request = Request(id, filters)
                relay.publish(request.to_message())
            else:
                raise RelayException(f"Invalid relay url: no connection to {relay.url}")

    def add_subscription_on_all_relays(self, id: str, filters: Filters):
        with self.lock:
            for relay in self.relays.values():
                if relay.policy.should_read:
                    relay.add_subscription(id, filters)
                    request = Request(id, filters)
                    relay.publish(request.to_message())

    def close_subscription_on_relay(self, url: str, id: str):
        with self.lock:
            if url in self.relays:
                relay = self.relays[url]
                relay.close_subscription(id)
                relay.publish(json.dumps(["CLOSE", id]))
            else:
                raise RelayException(f"Invalid relay url: no connection to {relay.url}")

    def close_subscription_on_all_relays(self, id: str):
        with self.lock:
            for relay in self.relays.values():
                relay.close_subscription(id)
                relay.publish(json.dumps(["CLOSE", id]))

    def close_all_relay_connections(self):
        with self.lock:
            for url in self.relays:
                relay = self.relays[url]
                relay.close()

    def publish_event(self, event: Event):
        """Verifies that the Event is publishable before submitting it to relays."""
        if event.signature is None:
            raise RelayException(f"Could not publish {event.id}: must be signed")

        if not event.verify():
            raise RelayException(
                f"Could not publish {event.id}: \
                failed to verify signature {event.signature}"
            )

        with self.lock:
            for relay in self.relays.values():
                if relay.policy.should_write:
                    relay.publish(event.to_message())
