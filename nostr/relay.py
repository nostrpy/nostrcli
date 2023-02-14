import json
import logging
import time
from dataclasses import dataclass
from threading import Lock
from typing import Optional

from websocket import (
    WebSocketApp,
    WebSocketConnectionClosedException,
    setdefaulttimeout,
)

from .event import Event
from .filter import Filters
from .message_pool import MessagePool
from .message_type import RelayMessageType
from .subscription import Subscription

logger = logging.getLogger("websocket")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

setdefaulttimeout(5)


@dataclass
class RelayPolicy:
    should_read: bool = True
    should_write: bool = True

    def to_json_object(self) -> "dict[str, bool]":
        return {"read": self.should_read, "write": self.should_write}


@dataclass
class RelayProxyConnectionConfig:
    host: Optional[str] = None
    port: Optional[int] = None
    type: Optional[str] = None


class Relay:
    def __init__(
        self,
        url: str,
        policy: RelayPolicy,
        message_pool: MessagePool,
        subscription: "dict[str, Subscription]" = None,
    ) -> None:
        self.url = url
        self.policy = policy
        self.message_pool = message_pool
        self.subscriptions = subscription or {}

        # self.proxy_config: RelayProxyConnectionConfig = RelayProxyConnectionConfig()

        self.lock: Lock = Lock()
        self.ws = WebSocketApp(
            url,
            on_open=self._on_open,
            on_message=self._on_message,
            # on_data=self._on_data,
            on_error=self._on_error,
            on_close=self._on_close,
            on_ping=self._on_ping,
            on_pong=self._on_pong,
        )
        self.active = False

    def connect(self, ssl_options: Optional[dict] = None):
        self.ws.run_forever(
            sslopt=ssl_options,
            # http_proxy_host=self.proxy_config.host,
            # http_proxy_port=self.proxy_config.port,
            # proxy_type=self.proxy_config.type
            ping_interval=60,
            ping_timeout=10,
            ping_payload="2",
            reconnect=30,
        )

    def close(self):
        self.ws.close()

    def publish(self, message: str):
        try:
            self.ws.send(message)
        except WebSocketConnectionClosedException:
            self.active = False
            logger.exception(f"failed to send message to {self.url}")

    def add_subscription(self, id, filters: Filters):
        with self.lock:
            self.subscriptions[id] = Subscription(id, filters)

    def close_subscription(self, id: str) -> None:
        with self.lock:
            self.subscriptions.pop(id)

    def update_subscription(self, id: str, filters: Filters) -> None:
        with self.lock:
            subscription = self.subscriptions[id]
            subscription.filters = filters

    def to_json_object(self) -> dict:
        return {
            "url": self.url,
            "policy": self.policy.to_json_object(),
            "subscriptions": [
                subscription.to_json_object()
                for subscription in self.subscriptions.values()
            ],
        }

    def _on_open(self, class_obj):
        self.active = time.time()
        print(f"OPEN: {self.url}")

    def _on_close(self, class_obj, status_code, message):
        print(f"CLOSE: {self.url} - {message}")
        self.active = False

    def _on_message(self, class_obj, message: str = None):
        self.active = time.time()
        if self._is_valid_message(message):
            self.message_pool.add_message(message, self.url)

    def _on_data(self, class_obj, message: str, data_type, continue_flag):
        print(f"DATA: {self.url} - {message}")

    def _on_error(self, class_obj, error):
        print(f"ERROR: {self.url}")

    def _on_ping(self, class_obj, message):
        pass

    def _on_pong(self, class_obj, message):
        self.active = time.time()

    def _is_valid_message(self, message: str) -> bool:
        message = message.strip("\n")
        if not message or message[0] != "[" or message[-1] != "]":
            return False

        message_json = json.loads(message)
        message_type = message_json[0]
        if not RelayMessageType.is_valid(message_type):
            return False

        if message_type == RelayMessageType.EVENT:
            if not len(message_json) == 3:
                return False

            subscription_id = message_json[1]
            with self.lock:
                if subscription_id not in self.subscriptions:
                    return False

            event = Event.from_dict(message_json[2])

            if not event.verify():
                return False

            with self.lock:
                subscription = self.subscriptions[subscription_id]

            if not subscription.filters.match(event):
                return False

        return True
