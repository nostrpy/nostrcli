import json
import unittest

from nostr.filter import Filter, Filters
from nostr.message_type import ClientMessageType
from nostr.subscription import Subscription


class TestSubscription(unittest.TestCase):
    def test_subscription_id(self):
        """check that subscription contents dump to JSON and load back to Python with
        expected types."""
        filters = Filters([Filter()])
        id = 123

        with self.assertRaisesRegex(TypeError, "Argument 'id' must be of type str"):
            subscription = Subscription(id=id, filters=filters)

        subscription = Subscription(id=str(id), filters=filters)
        request = [ClientMessageType.REQUEST, subscription.id]
        request.extend(subscription.filters.to_json_array())
        message = json.dumps(request)
        request_received = json.loads(message)
        message_type, subscription_id, req_filters = request_received
        self.assertTrue(isinstance(subscription_id, str))
        self.assertEqual(message_type, ClientMessageType.REQUEST)
        self.assertTrue(isinstance(req_filters, dict))
