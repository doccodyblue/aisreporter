import serial
import socket
import prometheus_client as prom
import logging
from datetime import datetime
from configparser import ConfigParser
from aisjson import AisAprs


config = ConfigParser()
config.read("aisreporter.ini")


def ConfigSectionMap(section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


debug = eval(ConfigSectionMap("generic")['debug'])
if debug == 1:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)

metrics = eval(ConfigSectionMap("generic")['metrics'])
if metrics == 1:
    prometheusport = eval(ConfigSectionMap("generic")['metricsport'])

marinetrafficenabled = eval(ConfigSectionMap("marinetraffic")['enabled'])
if marinetrafficenabled == 1:
    marinetrafficip = ConfigSectionMap("marinetraffic")['ip']
    marinetrafficport = eval(ConfigSectionMap("marinetraffic")['port'])

aishubenabled = eval(ConfigSectionMap("aishub")['enabled'])
if aishubenabled == 1:
    aishubip = ConfigSectionMap("aishub")['ip']
    aishubport = eval(ConfigSectionMap("aishub")['port'])

aprsenabled = eval(ConfigSectionMap("aprs")['enabled'])
if aprsenabled == 1:
    aprsurl = ConfigSectionMap("aprs")['url']
    aprsname = ConfigSectionMap("aprs")['name']

serialport = ConfigSectionMap("generic")['serialport']
serialbaud = eval(ConfigSectionMap("generic")['serialbaud'])


class SendAIS:
    # todo error handling if network is not reachable
    def __init__(self, ip, port):
        self.sentPackets = 0
        self.UDP_IP = ip
        self.UDP_PORT = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def sendframe(self, packetdata):
        self.sock.sendto(bytes(packetdata, "ASCII"), (self.UDP_IP, self.UDP_PORT))
        self.sentPackets += 1


class MetricsAis:
    def __init__(self, port):
        self.aissent = prom.Counter('ais_frames_forwarded', 'AIS packets forwarded')
        self.aiserror = prom.Counter('ais_decode_errors', 'AIS decode errors')
        self.aismissingmulti = prom.Counter('ais_decode_missingmultipart', 'AIS missing multipart')
        prom.start_http_server(port)

    def incais(self, value):
        self.aissent.inc(value)

    def incerror(self, value):
        self.aiserror.inc(value)

    def incmissingmulti(self, value):
        self.aismissingmulti.inc(value)

def timeprint(text):
    print(datetime.now(), ': ', text)


try:
    daisy = serial.Serial(serialport, serialbaud)
except:
    logging.error('Serial connection failed!')
    exit()

if marinetrafficenabled:
    marinetraffic = SendAIS(marinetrafficip, marinetrafficport)
    timeprint('MarineTraffic enabled')
    
if aishubenabled:
    aishub = SendAIS(aishubip, aishubport)
    timeprint('AISHub enabled')
    
if aprsenabled:
    aprs = AisAprs(aprsname, aprsurl)
    timeprint('APRS.fi enabled')

if metrics == 1:
    metric = MetricsAis(prometheusport)
    timeprint('Metrics enabled')
    
while 1:
    line = daisy.readline().decode('ASCII')
    if line[0:6] == '!AIVDM':
        if marinetrafficenabled == 1:
            marinetraffic.sendframe(line.strip())
            timeprint('S: MarineTraffic')
        if aishubenabled == 1:
            aishub.sendframe(line.strip())
            timeprint('S: AISHub')

        if aprsenabled == 1:
            jsonaprs = aprs.parsetojson(line)
            if jsonaprs == 'missing_multi':
                metric.incmissingmulti(1)
                timeprint('E: Missing multipart')
            else:
                aprs.sendframe(jsonaprs)
                timeprint('S: APRS.fi')


        if metrics == 1:
            metric.incais(1)

        logging.debug('received frame: %s', line)
    elif line[0:16] == 'error: RSSI drop':
        if metrics == 1:
            metric.incerror(1)
        logging.debug("RSSI Drop Error")
    elif line[0:16] == 'error: CRC error':
        if metrics == 1:
            metric.incerror(1)
        logging.debug("CRC failure")

daisy.close()
