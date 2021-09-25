import serial, socket
import prometheus_client as prom
import logging

logging.basicConfig(level=logging.DEBUG)

# port to have your metrics on
prometheusport = 9073

# set your marinetraffic.com ip and port assigned to your receiver
marinetrafficip = "5.9.207.224"
marinetrafficport = 6727

# serial ais device
serialport = '/dev/ttyACM0'
serialbaud = 57600


class SendAIS:
    def __init__(self, ip, port):
        self.sentPackets = 0
        self.UDP_IP = ip
        self.UDP_PORT = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def sendframe(self, packetdata):
        self.sock.sendto(bytes(packetdata, "ASCII"), (self.UDP_IP, self.UDP_PORT))
        self.sentPackets +=1

class MetricsAis:
    def __init__(self, port):
        self.aissent = prom.Counter('ais_frames_forwarded','AIS packets forwarded')
        self.aiserror = prom.Counter('ais_decode_errors','AIS decode errors')
        prom.start_http_server(port)

    def incais(self, value):
        self.aissent.inc(value)

    def incerror(self, value):
        self.aiserror.inc(value)


try:
    daisy = serial.Serial(serialport, serialbaud)
except:
    logger.error('Serial connection failed!')
    exit()


packetsend = SendAIS(marinetrafficip, marinetrafficport)
metric = MetricsAis(prometheusport)

while 1:
    line = daisy.readline().decode('ASCII')

    if (line[0] == '!'):
        packetsend.sendframe(line.strip())
        metric.incais(1)
        logging.debug('received frame: %s', line)
    elif (line[0:16] == 'error: RSSI drop'):
        metric.incerror(1)
        logging.debug("RSSI Drop Error")
    elif (line[0:16] == 'error: CRC error'):
        metric.incerror(1)
        logging.debug("CRC failure")

daisy.close()
