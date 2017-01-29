import json
import os
import unittest

from functools import wraps
import mock

from lambdas import my_pi_lambda

EVENTS = json.load(open(os.path.join(os.path.dirname(__file__), 'sample_events.json')))


def forall_events(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        for event_meta in EVENTS:
            kwds['event'] = event_meta['event']
            kwds['event_name'] = event_meta['name']
            return f(*args, **kwds)
    return wrapper


def find_event_by_name(name):
    for event_meta in EVENTS:
        if event_meta['name'] == name:
            return event_meta['event']
    raise KeyError(name)


class TestEventParsing(unittest.TestCase):
    @forall_events
    def test_get_intent(self, event, event_name):
        intent = my_pi_lambda.get_intent(event)
        self.assertTrue(intent.endswith('Intent'), 'Failed to parse intent in event {}'.format(event_name))

    def test_get_intent_failure(self):
        event = {
            'request': {
                'type': 'NotIntent'
            }
        }
        with self.assertRaises(ValueError):
            intent = my_pi_lambda.get_intent(event)

    @forall_events
    def test_get_slots(self, event, event_name):
        slots = my_pi_lambda.get_slots(event)
        self.assertIsInstance(slots, dict, 'Failed to parse slots in event {}'.format(event_name))

    def test_get_slots_play_3(self):
        event = find_event_by_name('PLAY_3')
        slots = my_pi_lambda.get_slots(event)
        self.assertEqual(slots, {'Number': '3'})


class TestPolishRadio(unittest.TestCase):
    def setUp(self):
        self.event = find_event_by_name('PLAY_3')

    def test_play(self):
        with mock.patch.object(my_pi_lambda.PiController, 'request_method') as request_mock:
            res = my_pi_lambda.lambda_handler(self.event, None)

        request_mock.assert_called()
        self.assertEqual(res['version'], '1.0')
        self.assertIn('response', res)



if __name__ == "__main__":
    unittest.main()
