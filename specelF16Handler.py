from aircraft import AircraftHandler
from dcsbiosParser import StringBuffer


class F16Handler(AircraftHandler):
    def __init__(self, displayHandler, parser):
        """
        Basic constructor.

        :param displayHandler:
        :param parser:
        """
        super().__init__(displayHandler, parser)
        self.DEDLine1 = ""
        self.DEDLine2 = ""
        self.DEDLine3 = ""
        self.DEDLine4 = ""
        self.DEDLine5 = ""

        self.bufferDEDLine1 = StringBuffer(parser, 0x44fc, 50, lambda s: self.setData("DEDLine1", s))
        self.bufferDEDLine2 = StringBuffer(parser, 0x452e, 50, lambda s: self.setData("DEDLine2", s))
        self.bufferDEDLine3 = StringBuffer(parser, 0x4560, 50, lambda s: self.setData("DEDLine3", s))
        self.bufferDEDLine4 = StringBuffer(parser, 0x4592, 50, lambda s: self.setData("DEDLine4", s))
        self.bufferDEDLine5 = StringBuffer(parser, 0x45c4, 50, lambda s: self.setData("DEDLine5", s))

    def updateDisplay(self):
        """Update display."""
        # clear bitmap
        self.draw.rectangle((0, 0, self.width, self.height), 0, 0)

        # print(self.DEDLine1)
        # print(self.DEDLine2)
        # print(self.DEDLine3)
        # print(self.DEDLine4)
        # print(self.DEDLine5)

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

        self.g13.updateDisplay(pixels)

    def setData(self, selector, value, update=True):
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
            self.updateDisplay()
