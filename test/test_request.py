import json
import unittest

from nostr.filter import Filter, Filters
from nostr.message_type import ClientMessageType
from nostr.request import Request
from nostr.subscription import Subscription


class TestRequest(unittest.TestCase):
    def test_request_id(self):
        """check that request contents dump to JSON and load back to Python with
        expected types."""
        filters = Filters([Filter()])
        id = 123

        subscription = Subscription(id=str(id), filters=filters)

        request = Request(subscription.id, filters)

        request_received = json.loads(request.to_message())
        message_type, subscription_id, req_filters = request_received
        self.assertTrue(isinstance(subscription_id, str))
        self.assertEqual(message_type, ClientMessageType.REQUEST)
        self.assertTrue(isinstance(req_filters, dict))
