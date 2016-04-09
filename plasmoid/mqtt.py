#!/usr/bin/env python


# mqtt to PiLite
# dpslwk 24/06/2013


import paho.mqtt.client as MQTT
import plasmoid.grove_rgb_lcd as LCD
import os, sys, time, Queue
import serial, threading
import itertools

lcd_rgb_colourmap={
    'base': [64,128,255],
    'good': [0,255,0],
    'warn': [255,255,0],
    'bad' : [255,0,0],
    'purple': [255,0,128],
    'white': [255,255,255]
}
lcd_rgb_colourmap.update({
    'info' : lcd_rgb_colourmap['base'],
    'err' : lcd_rgb_colourmap['bad'],
    'debug': lcd_rgb_colourmap['purple']
})


class PlasmoidMQTTHandler:
    # publish from Pi-LITE topic
    p_rx = "pilite/from"

    # serial port for URF
    port = "/dev/ttyAMA0"

    MQTTServer = "bolster.online"
    clientName = "Plasmoid Bridge"

    def __init__(self):
        self.queue = Queue.Queue()
        self.s = serial.Serial()
        self.t = threading.Thread(target=self.run)
        # open serial port to PiLite
        self.s.baudrate = 9600
        self.s.timeout = 0
        self.connect()

        # Setup Grove LCD Connection
        LCD.setRGB(64,64,64)
        LCD.setText("")

        # mqtt setup on
        self.client = MQTT.Client(self.clientName)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.callbacks = {
            "pilite/text": self.push_to_pilite,
            "grove/text": self.push_to_grove_lcd,
            "grove/scroll": self.scroll_to_grove_lcd,
            "grove/rgb": self.set_grove_rgb
        }
        for topic,callback in self.callbacks.items():
            self.client.message_callback_add(topic, callback)

        self.client.connect(self.MQTTServer)

        self.client.subscribe(zip(self.callbacks.keys(), itertools.repeat(0)))

    def __del__(self):
        self.disconnect_all()

    def connect(self):
        if self.s.isOpen() == False:
            self.s.port = self.port
            try:
                self.s.open()
            except serial.SerialException, e:
                sys.stderr.write("could not open port %r: %s\n" % (self.port, e))
                sys.exit(1)
            # start the read thread
            self.t.start()
            return True
        else:
            return False

    def disconnect(self):
        # closeing the serial port will stop the thread
        if self.s.isOpen() == True:
            self.s.close()

    def run(self):
        while self.s.isOpen() == True:
            if self.s.inWaiting():
                msg = self.s.read()
                print(msg)
                self.queue.put(msg)
            time.sleep(0.1)  # may need adjusting

    def sendLLAP(self, llapMsg):
        while len(llapMsg) < 12:
            llapMsg += '-'
        if self.s.isOpen() == True:
            self.s.write(llapMsg)

    def main(self):
        # loop
        rc = 0
        try:
            while rc == 0:
                # mqtt stuff
                rc = self.client.loop()
                # serial stuff
                self.decodeLLAP()
            # we lost the network to mqtt
            print("We lost MQTT")
        except KeyboardInterrupt:
            print("Keyboard Quit")
            self.disconnect_all()

    def disconnect_all(self):

        self.client.unsubscribe(self.callbacks.keys())
        self.client.loop()
        self.client.disconnect()
        self.client.loop()
        self.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected successfully.")

    def on_disconnect(self, client, userdata, rc):
        if rc == 1:
            # unexpected disconnect, reconnect?
            pass
        else:
            # expected disconnect
            print("Disconnected successfully.")

    def on_message(self, mosq, obj, msg):
        # got mqtt message to send
        print("Message received on topic " + msg.topic + " with QoS " + str(msg.qos) + " and payload " + msg.payload)
        # push to serial

    def push_to_pilite(self, mosq, obj, msg):
        print("Message received on topic " + msg.topic + " with QoS " + str(msg.qos) + " and payload " + msg.payload + " To PiLite")
        self.s.write(msg.payload)

    def push_to_grove_lcd(self, mosq, obj, msg):
        print("Message received on topic " + msg.topic + " with QoS " + str(msg.qos) + " and payload " + msg.payload + " To Grove")
        LCD.setText(msg.payload)

    def set_grove_rgb(self, mosq, obj, msg):
        print("Message received on topic " + msg.topic + " with QoS " + str(msg.qos) + " and payload " + msg.payload + " To Grove")
        try:
            r,g,b = map(int,msg.payload.split(','))
            LCD.setRGB(r,g,b)
        except (ValueError, AttributeError):
            # Noone gives a shit if you can't do it properly
            if msg.payload in lcd_rgb_colourmap:
                LCD.setRGB(*lcd_rgb_colourmap[msg.payload])
            else:
                pass

    def scroll_to_grove_lcd(self, mosq, obj, msg):
        print("Message received on topic " + msg.topic + " with QoS " + str(msg.qos) + " and payload " + msg.payload + " To Grove")
        LCD.scrollableTopLineText(msg.payload)

    def decodeLLAP(self):
        if not self.queue.empty():
            msg = self.queue.get()
            # publish to mqtt
            self.client.publish(self.p_rx, msg)
            self.queue.task_done()

        return True


