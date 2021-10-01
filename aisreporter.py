import serial
import socket
import prometheus_client as prom
import logging
import time
from datetime import datetime
from configparser import ConfigParser
from aisjson import AisAprs
from statistics import mean


config = ConfigParser()
config.read("aisreporter.ini")


def configsectionmap(section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


debug = eval(configsectionmap("generic")['debug'])
if debug == 1:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)

metrics = eval(configsectionmap("generic")['metrics'])
if metrics == 1:
    prometheusport = eval(configsectionmap("generic")['metricsport'])

marinetrafficenabled = eval(configsectionmap("marinetraffic")['enabled'])
if marinetrafficenabled == 1:
    marinetrafficip = configsectionmap("marinetraffic")['ip']
    marinetrafficport = eval(configsectionmap("marinetraffic")['port'])

aishubenabled = eval(configsectionmap("aishub")['enabled'])
if aishubenabled == 1:
    aishubip = configsectionmap("aishub")['ip']
    aishubport = eval(configsectionmap("aishub")['port'])

aprsenabled = eval(configsectionmap("aprs")['enabled'])
if aprsenabled == 1:
    aprsurl = configsectionmap("aprs")['url']
    aprsname = configsectionmap("aprs")['name']

serialport = configsectionmap("generic")['serialport']
serialbaud = eval(configsectionmap("generic")['serialbaud'])


class SendAIS:
    def __init__(self, ip, port):
        self.sentPackets = 0
        self.UDP_IP = ip
        self.UDP_PORT = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def sendframe(self, packetdata):
        try:
            self.sock.sendto(bytes(packetdata, "ASCII"), (self.UDP_IP, self.UDP_PORT))
            self.sentPackets += 1
        except socket.error:
            timeprint('E: socket.error in sendframe - waiting for 60 sec ')
            time.sleep(60)
        except Exception as e:
            timeprint(e)


class MetricsAis:
    def __init__(self, port):
        self.aissent = prom.Counter('ais_frames_forwarded', 'AIS packets forwarded')
        self.aiserror = prom.Counter('ais_decode_errors', 'AIS decode errors')
        self.aismissingmulti = prom.Counter('ais_decode_missingmultipart', 'AIS missing multipart')
        self.packetsperminute = prom.Gauge('ais_packets_per_minute', 'AIS received ppm rate')
        prom.start_http_server(port)

    def incais(self, value):
        self.aissent.inc(value)

    def incerror(self, value):
        self.aiserror.inc(value)

    def incmissingmulti(self, value):
        self.aismissingmulti.inc(value)

    def packetrate(self, value):
        self.packetsperminute.set(value)


class ThingsPerMinute:
    def __init__(self):
        self.timestamp = datetime.today().timestamp()
        self.timestamp_last = self.timestamp
        self.rate = 0
        self.timeperpacketaverage = []

    def update(self, inc):
        timestamp_now = datetime.today().timestamp()
        timedifference = timestamp_now - self.timestamp_last
        self.timeperpacketaverage.append(timedifference)

        self.timestamp_last = timestamp_now
        if len(self.timeperpacketaverage) > 100:
            self.timeperpacketaverage.pop(0)

        self.rate = round(60 / mean(self.timeperpacketaverage), 1)
        return self.rate

    def ask(self):
        return self.rate


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

rate = ThingsPerMinute()

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

        rate.update(1)

        if metrics == 1:
            metric.incais(1)
            x = rate.ask()
            metric.packetrate(x)

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
