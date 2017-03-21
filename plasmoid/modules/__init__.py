import json

class PlasmoidModule(object):
    callbacks = {}
    actions = {}
    producers = {}
    def get_actions(self):
        return self.actions.keys()

    def get_message_handler(cls, callback):
        print("Getting handler for {}".format(callback))
        def hdlr(mosq, obj, msg):
            print("Message to {callback} received on topic {topic} with QoS {qos} and payload {payload} ".format(
                callback=callback, topic=msg.topic, payload=msg.payload, qos=msg.qos))
            try:
                callback(**json.loads(msg.payload))
            except ValueError:
                callback(msg.payload)

        return hdlr

    def check_producers(self):
        for topic, producer in self.producers.items():
            yield (topic, json.dumps(producer()))

    def add_producer(self, topic, producer):
        self.producers.update({topic:producer})

    def remove_producer(self, topic):
        try:
            del self.producers[topic]
        except AttributeError:
            pass