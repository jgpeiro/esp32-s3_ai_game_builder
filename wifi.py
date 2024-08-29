import time
import network

def connect(ssid, pswd):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, pswd)
        while not wlan.isconnected():
            pass
    return wlan.ifconfig()[0]