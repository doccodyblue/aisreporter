Simple Python code to receive AIS packets from serial receiver and push them to marinetraffic.com or AisHub (or other services accepting RAW streams)

It was used with the dAISy AIS receiver but should work with any receiver sending out !AIVDM frames on a serial port.
Other frames will be ignored.

Optional you will receive a prometheus metric on port 9073 for monitoring

Installation:
Don't forget to change your assigned IP address and UDP port for marinetraffic.com / AisHub in the aisreporter.ini
Also edit serial port and baud rate


