#!/usr/bin/env python



import paho.mqtt.client as MQTT

import os, sys, time, Queue
import serial, threading
import itertools
from time import time, sleep

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

LCD=None

def LCD(*args,**kwargs):
    raise NotImplementedError("No LCD Configured!")

class PlasmoidMQTTHandler:

    MQTTServer = "bolster.online"
    clientName = "Plasmoid Bridge"
    pilite_bar = []

    production_period = 10
    sample_period = 0.1
    production_counter = production_period

    def __init__(self, modules=[]):
        # publish from Pi-LITE topic
        self.p_rx = "pilite/from"

        # serial port for URF
        self.port = "/dev/ttyAMA0"
        self.queue = Queue.Queue()
        self.s = serial.Serial()
        self.t = threading.Thread(target=self.run)
        # open serial port to PiLite
        self.s.baudrate = 9600
        self.s.timeout = 0
        self.connect()

        self.callbacks = {}
        self.modules=[]

        # mqtt setup on
        self.client = MQTT.Client(self.clientName)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        for module in modules:
            self.add_module(module)

        for topic,callback in self.callbacks.items():
            print("Adding Callback {}:{}".format(topic,callback))
            self.client.message_callback_add(topic, callback)

        self.client.connect(self.MQTTServer)

        self.client.subscribe(zip(self.callbacks.keys(), itertools.repeat(0)))

    def __del__(self):
        self.disconnect_all()

    def add_module(self, module):
        self.callbacks.update(module.callbacks)
        self.modules.append(module)

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
        t_last_prod = time()+self.production_period
        while self.s.isOpen() == True:
            if self.s.inWaiting():
                msg = self.s.read()
                print(msg)
                self.queue.put(msg)
            sleep(0.1)  # may need adjusting
            if t_last_prod < round(time() - self.production_period):
                for m in self.modules:
                    for topic, payload in m.check_producers():
                        if topic is not None:
                            self.client.publish(topic, payload)
                t_last_prod = time()


    def sendLLAP(self, llapMsg):
        while len(llapMsg) < 12:
            llapMsg += '-'
        if self.s.isOpen() == True:
            self.s.write(llapMsg)

    def main(self):
        # loop
        rc = 0
        rc_dict = {
        0: "Connection successful",
        1: "Connection refused - incorrect protocol version",
        2: "Connection refused - invalid client identifier",
        3: "Connection refused - server unavailable",
        4: "Connection refused - bad username or password",
        5: "Connection refused - not authorised"
        }
        try:
            while rc == 0 or rc == 3:
                # mqtt stuff
                rc = self.client.loop()
                # serial stuff
                self.decodeLLAP()
            print rc_dict[rc]
        except (KeyboardInterrupt, SystemExit):
            print("Quit")
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



    def update_pilite_bar(self, mosq, obj,msg):
        print("Message received on topic " + msg.topic + " with QoS " + str(msg.qos) + " and payload " + msg.payload + " To PiLiteBar")
        if len(self.pilite_bar)>14:
            self.pilite_bar.pop(0)
        try:
            self.pilite_bar.append(msg.payload)
            self.set_pilite_bar()
        except:
            print("That didn't work; {}".format(msg))

    def set_pilite_bar(self):
        print self.pilite_bar
        for i,v in enumerate(self.pilite_bar):
            s = "$$$B{},{}\r".format(i+1,v)
            print s
            self.s.write(s)




    def scroll_to_grove_lcd(self, mosq, obj, msg):
        print("Message received on topic " + msg.topic + " with QoS " + str(msg.qos) + " and payload " + msg.payload + " To Grove")

        if self.has_lcd:
            LCD.scrollableTopLineText(msg.payload)

    def decodeLLAP(self):
        if not self.queue.empty():
            msg = self.queue.get()
            # publish to mqtt
            self.client.publish(self.p_rx, msg)
            self.queue.task_done()

        return True


