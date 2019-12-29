from aircraft import AircraftHandler
from dcsbiosParser import StringBuffer


class F16Handler(AircraftHandler):
    def __init__(self, display_handler, parser):
        """
        Basic constructor.

        :param display_handler:
        :param parser:
        """
        super().__init__(display_handler, parser)
        self.DEDLine1 = ""
        self.DEDLine2 = ""
        self.DEDLine3 = ""
        self.DEDLine4 = ""
        self.DEDLine5 = ""

        self.bufferDEDLine1 = StringBuffer(parser, 0x44fc, 50, lambda s: self.set_data("DEDLine1", s))
        self.bufferDEDLine2 = StringBuffer(parser, 0x452e, 50, lambda s: self.set_data("DEDLine2", s))
        self.bufferDEDLine3 = StringBuffer(parser, 0x4560, 50, lambda s: self.set_data("DEDLine3", s))
        self.bufferDEDLine4 = StringBuffer(parser, 0x4592, 50, lambda s: self.set_data("DEDLine4", s))
        self.bufferDEDLine5 = StringBuffer(parser, 0x45c4, 50, lambda s: self.set_data("DEDLine5", s))

    def update_display(self):
        """Update display."""
        super().update_display()

        pos = 0
        offsetpos = 8
        self.draw.text((0, pos), self.DEDLine1, 1, self.font1)
        pos = pos + offsetpos
        self.draw.text((0, pos), self.DEDLine2, 1, self.font1)
        pos = pos + offsetpos
        self.draw.text((0, pos), self.DEDLine3, 1, self.font1)
        pos = pos + offsetpos
        self.draw.text((0, pos), self.DEDLine4, 1, self.font1)
        pos = pos + offsetpos
        self.draw.text((0, pos), self.DEDLine5, 1, self.font1)

        # make it array and set proper values
        pixels = list(self.img.getdata())
        for i in range(0, len(pixels)):
            pixels[i] *= 128

        self.g13.update_display(pixels)

    def set_data(self, selector, value, update=True):
        """
        Set new data.

        :param selector:
        :param value:
        :param update:
        """
        # programming noob here, but it's pretty clear how to use this monster
        if selector == "DEDLine1":
            self.DEDLine1 = value
        elif selector == "DEDLine2":
            self.DEDLine2 = value
        elif selector == "DEDLine3":
            self.DEDLine3 = value
        elif selector == "DEDLine4":
            self.DEDLine4 = value
        elif selector == "DEDLine5":
            self.DEDLine5 = value
        else:
            print("No such selector: ", selector)

        if update:
            self.update_display()
