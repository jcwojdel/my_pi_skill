import datetime
import hashlib
import httplib
import json
import base64
import os

SECRET = os.environ['SECRET']
HOST = os.environ['HOST']


def get_intent(event):
    if event['request']['type'] != 'IntentRequest':
        raise ValueError('Event does not correspond to intent request', event)
    return event['request']['intent']['name'].replace('.', '')


def get_slots(event):
    slots = {}
    event_slot_dict = event['request']['intent'].get('slots', {})

    for slot_name, slot_dict in event_slot_dict.items():
        slots[slot_name] = slot_dict.get('value', None)

    return slots


def get_session_attrs(event):
    return event.get('session', {}).get('attributes', {})


class RadioController(object):
    def PlayPolishRadioIntent(self, Number):
        if Number is None:
            return self.ask_for_details('Which Polish radio would you like to play?', session_attr={'Context': 'Radio'})

        channel_num = int(Number)
        if 1 <= channel_num <= 4:
            url = 'http://stream3.polskieradio.pl:890{}/listen.pls'.format(2 * (channel_num - 1))
        else:
            return self.ask_for_details('I dont know this radio. Which other Polish radio would you like to play?',
                                        session_attr={'Context': 'Radio'})

        self.request_method('Player.Open', item={'file': url})

        return self.respond_simple_text('Playing Polish Radio {}'.format(Number))

    def AMAZONStopIntent(self):
        active_players = self.request_method('Player.GetActivePlayers')
        self.request_method('Player.Stop', playerid=active_players[0]['playerid'])

        return self.respond_simple_text('Stopped playing radio')

    def SetVolumeIntent(self, Number):
        if Number is None:
            return self.ask_for_details('What volume percentage would you like to set?',
                                        session_attr={'Context': 'Volume'})

        self.request_method('Application.SetVolume', volume=int(Number))

        return self.respond_simple_text('Volume set to {}'.format(Number))

    def AmbiguousNumberIntent(self, Number):
        context = self.session_attributes.get('Context')
        if context == 'Radio':
            return self.PlayPolishRadioIntent(Number)
        if context == 'Volume':
            return self.SetVolumeIntent(Number)

        return self.ask_for_details('I did not understand what you meant. What do you want my pie to do?')

    def VolumeUpIntent(self):
        current_properties = self.request_method('Application.GetProperties', properties=['volume'])
        current_volume = int(current_properties['volume'])
        desired_volume = min(current_volume + 10, 100)
        self.request_method('Application.SetVolume', volume=desired_volume)

        return self.respond_simple_text('Raised volume to {}'.format(desired_volume))

    def VolumeDownIntent(self):
        current_properties = self.request_method('Application.GetProperties', properties=['volume'])
        current_volume = int(current_properties['volume'])
        desired_volume = max(current_volume - 10, 0)
        self.request_method('Application.SetVolume', volume=desired_volume)

        return self.respond_simple_text('Lowered volume to {}'.format(desired_volume))

    def MaxVolumeIntent(self):
        self.request_method('Application.SetVolume', volume=100)

        return self.respond_simple_text('Volume set to maximum')

    def MuteIntent(self):
        self.request_method('Application.SetMute', mute=True)

        return self.respond_simple_text('Radio muted')

    def UnMuteIntent(self):
        self.request_method('Application.SetMute', mute=False)

        return self.respond_simple_text('Radio unmuted')


class SkillController(object):
    def process_event(self, event):
        intent = get_intent(event)
        slots = get_slots(event)
        self.session_attributes = get_session_attrs(event)
        return self.dispatch_intent(intent, slots)

    def dispatch_intent(self, intent, slots):
        return self.__getattribute__(intent)(**slots)

    def ask_for_details(self, text, session_attr=None):
        data = self.respond_simple_text(text)
        data["response"]["shouldEndSession"] = False
        data['sessionAttributes'] = session_attr or {}
        return data

    def respond_simple_text(self, text):
        data = {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": text
                },
                "card": {
                    "type": "Simple",
                    "title": "My PI",
                    "content": text
                }
            }
        }

        return data


class PiController(object):
    def build_jsonrpc(self, method_name, **kwargs):
        rpc = {
            "jsonrpc": "2.0",
            "method": method_name,
            "id": '{} - {}'.format(datetime.datetime.now(), method_name)
        }
        if kwargs:
            rpc['params'] = kwargs

        return rpc

    def build_current_password(self, offset):
        date = (datetime.datetime.utcnow() + offset).strftime('%Y%m%d%H')
        print 'Using date {}'.format(date)
        seeded_secret = '{}{}'.format(date, SECRET)
        md5 = hashlib.md5(seeded_secret)
        return md5.hexdigest()

    def post_data(self, data, minutes):
        offset = datetime.timedelta(minutes=minutes)
        password = self.build_current_password(offset)
        auth = base64.b64encode('kodi:{}'.format(password))
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Basic {}'.format(auth)
        }
        conn = httplib.HTTPConnection(HOST)
        conn.request('POST', '/jsonrpc', json.dumps(data), headers)
        response = conn.getresponse()
        return response

    def request_method(self, method_name, **kwargs):
        data = self.build_jsonrpc(method_name, **kwargs)
        for minutes in [-5, 0, 5]:
            response = self.post_data(data, minutes)

            if response.status == 401:
                continue

            if response.status != 200:
                raise Exception('Failure to communicate with PI: {} - {}'.format(response.status, response.reason))

            ret_data = json.loads(response.read())

            # Yes, all of the above is:
            #basic_auth = requests.auth.HTTPBasicAuth('kodi', password)
            #res = requests.post('http://wojdel.ddns.net/jsonrpc', json=data, auth=basic_auth)
            #ret_data = res.json()

            if 'error' in ret_data:
                raise Exception(ret_data['error'])

            return ret_data['result']

        raise Exception('Failure to communicate with PI: {} - {}'.format(response.status, response.reason))


class MyPiRadioSkill(RadioController, PiController, SkillController):
    pass


def lambda_handler(event, context):
    pc = MyPiRadioSkill()
    return pc.process_event(event)
