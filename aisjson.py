import json
import datetime
import requests
import logging
import pyais



class AisAprs:
    def __init__(self, call, url):
        self.sentPackets = 0
        self.call = call
        self.url = url
        self.conerror = 0

    def parsetojson(self, frame):
        try:
            msg = pyais.decode_msg(frame)
        except pyais.exceptions.MissingMultipartMessageException:
            return 'missing_multi'

        except Exception as e:  # todo needs proper error handling
            print(e)
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
            r = requests.post(self.url, files={'jsonais': (None, post)}, timeout=2)

        except requests.exceptions.ConnectionError:
            self.conerror +=1
            logging.warning('Connection error %s while connecting %s - not giving up', self.conerror, self.url)

        except requests.exceptions.RequestException as e:
            logging.warning('Request error while connecting %s - %s', self.url, e)

        else:
            self.conerror = 0
            if r.status_code == 200:
                return 1

