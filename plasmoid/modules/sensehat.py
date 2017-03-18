from plasmoid.modules import PlasmoidModule
from sense_hat import SenseHat as _SenseHat

from time import time, sleep

class SenseHat(PlasmoidModule):
    def __init__(self):
        self.sense = _SenseHat()
        self.callbacks = {
            'show_message': self.get_message_handler(self.sense.show_message),
            'set_rotation': self.get_message_handler(self.sense.set_rotation),
            'rainbow':self.get_message_handler(lambda m: rainbow(self.sense))
        }
        self.add_producer('environment', self.environment_info)
        self.add_producer(None, self.autorotate)

    def autorotate(self):
        self.sense.set_rotation(
            rotation_from_orientation(
                **self.sense.get_accelerometer_raw()
            )
        )

    def environment_info(self):
        return get_environment_info(self.sense)

def rotation_from_orientation(**kwargs):
    x = round(kwargs['x'], 0)
    y = round(kwargs['y'], 0)

    rot = 0
    if y == -1:
        rot = 90
    elif x == 1:
        rot = 180
    elif y == 1:
        rot = 270

    return rot

def get_environment_info(sh):
    ret = {
        'temperature': min(sh.get_temperature_from_humidity(),sh.get_temperature_from_pressure()),
        'humidity': sh.get_humidity(),
        'pressure': sh.get_pressure()
    }
    return ret


def rainbow(sense):
    pixels = [
        [255, 0, 0], [255, 0, 0], [255, 87, 0], [255, 196, 0], [205, 255, 0], [95, 255, 0], [0, 255, 13], [0, 255, 122],
        [255, 0, 0], [255, 96, 0], [255, 205, 0], [196, 255, 0], [87, 255, 0], [0, 255, 22], [0, 255, 131],
        [0, 255, 240],
        [255, 105, 0], [255, 214, 0], [187, 255, 0], [78, 255, 0], [0, 255, 30], [0, 255, 140], [0, 255, 248],
        [0, 152, 255],
        [255, 223, 0], [178, 255, 0], [70, 255, 0], [0, 255, 40], [0, 255, 148], [0, 253, 255], [0, 144, 255],
        [0, 34, 255],
        [170, 255, 0], [61, 255, 0], [0, 255, 48], [0, 255, 157], [0, 243, 255], [0, 134, 255], [0, 26, 255],
        [83, 0, 255],
        [52, 255, 0], [0, 255, 57], [0, 255, 166], [0, 235, 255], [0, 126, 255], [0, 17, 255], [92, 0, 255],
        [201, 0, 255],
        [0, 255, 66], [0, 255, 174], [0, 226, 255], [0, 117, 255], [0, 8, 255], [100, 0, 255], [210, 0, 255],
        [255, 0, 192],
        [0, 255, 183], [0, 217, 255], [0, 109, 255], [0, 0, 255], [110, 0, 255], [218, 0, 255], [255, 0, 183],
        [255, 0, 74]
    ]

    msleep = lambda x: sleep(x / 1000.0)

    def next_colour(pix):
        r = pix[0]
        g = pix[1]
        b = pix[2]

        if (r == 255 and g < 255 and b == 0):
            g += 1

        if (g == 255 and r > 0 and b == 0):
            r -= 1

        if (g == 255 and b < 255 and r == 0):
            b += 1

        if (b == 255 and g > 0 and r == 0):
            g -= 1

        if (b == 255 and r < 255 and g == 0):
            r += 1

        if (r == 255 and b > 0 and g == 0):
            b -= 1

        pix[0] = r
        pix[1] = g
        pix[2] = b

    t_start = time()
    while (time()-10)<t_start:
        for pix in pixels:
            next_colour(pix)

        sense.set_pixels(pixels)
