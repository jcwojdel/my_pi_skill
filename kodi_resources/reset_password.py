import xbmc
import json
import datetime
import hashlib

SECRET = PLACE_A_SECRET_HERE


def build_current_password():
    date = datetime.datetime.utcnow().strftime('%Y%m%d%H')
    seeded_secret = '{}{}'.format(date, SECRET)
    md5 = hashlib.md5(seeded_secret)
    return md5.hexdigest()


def call_json_rpc():
    method = 'Settings.SetSettingValue'
    password = build_current_password()
    jsonrpc = {
        'jsonrpc': '2.0',
        'method': method,
        'params': {
            'setting': 'services.webserverpassword',
            'value': password
        },
        'id': '{} - {}'.format(datetime.datetime.utcnow(), method)
    }

    call = json.dumps(jsonrpc)

    xbmc.executeJSONRPC(call)
    print 'Setting password to {}'.format(password)

call_json_rpc()
