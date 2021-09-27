import json
import ais.stream
import datetime
import requests


class AisAprs:
    def __init__(self, call, url):
        self.sentPackets = 0
        self.call = call
        self.url = url

    def parsetojson(self, frame):
        msg = ais.stream.decode(frame, keep_nmea=True)
        rxtime = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")  # YYYYMMDDHHMMSS
        parsed = json.loads(json.dumps(msg))

        aisframe = {
            'msgtype': parsed['id'],
            'mmsi': parsed['mmsi'],
            'rxtime': rxtime
        }

        if 'x' in parsed:
            aisframe['lon'] = parsed['x']
        if 'y' in parsed:
            aisframe['lat'] = parsed['y']
        if 'sog' in parsed:
            aisframe['speed'] = parsed['sog']
        if 'cog' in parsed:
            aisframe['course'] = parsed['cog']
        if 'true_heading' in parsed:
            aisframe['heading'] = parsed['true_heading']
        if 'nav_status' in parsed:
            aisframe['status'] = parsed['nav_status']
        if 'type_and_cargo' in parsed:
            aisframe['shiptype'] = parsed['type_and_cargo']
        if 'part_num' in parsed:
            aisframe['partno'] = parsed['part_num']
        if 'callsign' in parsed:
            aisframe['callsign'] = parsed['callsign']
        if 'name' in parsed:
            aisframe['shipname'] = parsed['name']
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

    def aprssendframe(self, post):
        try:
            r = requests.post(self.url, files={'jsonais': (None, post)})
        except requests.exceptions.RequestException as e:
            print(e)


