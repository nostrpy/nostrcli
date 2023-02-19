import json
from dataclasses import dataclass
from queue import Queue
from threading import Lock
from typing import List, Optional

from .event import Event
from .message_type import RelayMessageType


class EventMessage:
    def __init__(self, event: Event, subscription_id: str, url: str) -> None:
        self.event = event
        self.subscription_id = subscription_id
        self.url = url

    def __repr__(self):
        return f'EventMessage({self.url}: kind {str(self.event.kind)})'


class NoticeMessage:
    def __init__(self, content: str, url: str) -> None:
        self.content = content
        self.url = url

    def __repr__(self):
        return f'Notice({self.url}: {self.content})'


class EndOfStoredEventsMessage:
    def __init__(self, subscription_id: str, url: str) -> None:
        self.subscription_id = subscription_id
        self.url = url

    def __repr__(self):
        return f'EOSE({self.url})'


class OkMessage:
    def __init__(self, content: str, url: str) -> None:
        self.content = content
        self.url = url


class MessagePool:
    def __init__(self) -> None:
        self.events: Queue[EventMessage] = Queue()
        self.notices: Queue[NoticeMessage] = Queue()
        self.eose_notices: Queue[EndOfStoredEventsMessage] = Queue()
        self.ok_notices: Queue[OkMessage] = Queue()
        self._unique_events: set = set()
        self.lock: Lock = Lock()

    def add_message(self, message: str, url: str):
        self._process_message(message, url)

    def get_all(self):
        results = {"events": [], "notices": [], "eose": [], "ok": []}
        while self.has_events():
            results["events"].append(self.get_event())
        while self.has_notices():
            results["notices"].append(self.get_notice())
        while self.has_eose_notices():
            results["eose"].append(self.get_eose_notice())
        while self.has_ok_notices():
            results["ok"].append(self.get_ok_notice())
        return results

    def get_event(self):
        return self.events.get()

    def get_notice(self):
        return self.notices.get()

    def get_eose_notice(self):
        return self.eose_notices.get()

    def get_ok_notice(self):
        return self.ok_notices.get()

    def has_events(self):
        return self.events.qsize() > 0

    def has_notices(self):
        return self.notices.qsize() > 0

    def has_eose_notices(self):
        return self.eose_notices.qsize() > 0

    def has_ok_notices(self):
        return self.ok_notices.qsize() > 0

    def _process_message(self, message: str, url: str):
        message_json = json.loads(message)
        message_type = message_json[0]
        if message_type == RelayMessageType.EVENT:
            subscription_id = message_json[1]
            event = Event.from_dict(message_json[2])
            with self.lock:
                uid = subscription_id + event.id
                if uid not in self._unique_events:
                    self.events.put(EventMessage(event, subscription_id, url))
                    self._unique_events.add(uid)
        elif message_type == RelayMessageType.NOTICE:
            self.notices.put(NoticeMessage(message_json[1], url))
        elif message_type == RelayMessageType.END_OF_STORED_EVENTS:
            self.eose_notices.put(EndOfStoredEventsMessage(message_json[1], url))
        elif message_type == RelayMessageType.OK:
            self.ok_notices.put(OkMessage(message, url))

    def __repr__(self):
        return (
            f'Pool(events({self.events.qsize()}) '
            f'notices({self.notices.qsize()}) '
            f'eose({self.eose_notices.qsize()})) '
            f'ok({self.ok_notices.qsize()}))'
        )


@dataclass
class EventMessageStore:
    eventMessages: Optional[List[EventMessage]] = None

    def add_event(self, event):
        if self.eventMessages is None:
            self.eventMessages = []
        if isinstance(event, list):
            self.eventMessages += event
        else:
            self.eventMessages.append(event)

    def get_newest_event(self):
        if not self.eventMessages:
            return None
        return max(self.eventMessages, key=lambda x: x.event.date_time())

    def get_events_by_url(self, url):
        return [event for event in self.eventMessages if event.url == url]

    def get_events_by_id(self, subscription_id):
        return [
            event
            for event in self.eventMessages
            if event.subscription_id == subscription_id
        ]

    def __repr__(self):
        if not self.eventMessages:
            return 'EventMessageStore()'
        return f'EventMessageStore({len(self.eventMessages)} events)'
