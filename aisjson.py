import json
import datetime
import requests
from pyais import decode_msg


class AisAprs:
    def __init__(self, call, url):
        self.sentPackets = 0
        self.call = call
        self.url = url

    def parsetojson(self, frame):
        try:
            msg = decode_msg(frame)
        except:  # todo needs proper error handling
            return

        rxtime = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")

        parsed = json.loads(json.dumps(msg))
        aisframe = {
            'msgtype': parsed['type'],
            'mmsi': parsed['mmsi'],
            'rxtime': rxtime
        }

        if 'lon' in parsed:
            aisframe['lon'] = parsed['lon']
        if 'lat' in parsed:
            aisframe['lat'] = parsed['lat']
        if 'speed' in parsed:
            aisframe['speed'] = parsed['speed']
        if 'course' in parsed:
            aisframe['course'] = parsed['course']
        if 'heading' in parsed:
            aisframe['heading'] = parsed['heading']
        if 'status' in parsed:
            aisframe['status'] = parsed['status']
        if 'shiptype' in parsed:
            aisframe['shiptype'] = parsed['shiptype']
        if 'part_num' in parsed:
            aisframe['partno'] = parsed['part_num']
        if 'callsign' in parsed:
            aisframe['callsign'] = parsed['callsign']
        if 'shipname' in parsed:
            aisframe['shipname'] = parsed['shipname']
        if 'vendor_id' in parsed:
            aisframe['vendorid'] = parsed['vendor_id']
        if 'dim_a' in parsed:
            aisframe['ref_front'] = parsed['dim_a']
        if 'dim_c' in parsed:
            aisframe['ref_left'] = parsed['dim_c']
        if 'draught' in parsed:
            aisframe['draught'] = parsed['draught']
        if 'length' in parsed:
            aisframe['length'] = parsed['length']
        if 'width' in parsed:
            aisframe['width'] = parsed['width']
        if 'destination' in parsed:
            aisframe['destination'] = parsed['destination']
        if 'persons' in parsed:
            aisframe['persons_on_board'] = parsed['persons']

        path = {
            "name": self.call,
            "url": self.url}

        groups = {
            "path": [path],
            "msgs": [aisframe]}

        output = {
            "encodetime": rxtime,
            "protocol": 'jsonais',
            "groups": [groups]
        }

        post = json.dumps(output)
        return post

    def sendframe(self, post):
        try:
            r = requests.post(self.url, files={'jsonais': (None, post)})
        except requests.exceptions.RequestException as e:
            print(e)


