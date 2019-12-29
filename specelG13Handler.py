from ctypes import c_ubyte, sizeof, c_voidp
from platform import architecture
from socket import socket
from sys import maxsize
from typing import List

from PIL import Image, ImageFont, ImageDraw

import GLCD_SDK
from dcsbiosParser import StringBuffer, ProtocolParser
from specelF16Handler import F16Handler
from specelFA18Handler import FA18Handler


class G13Handler:
    def __init__(self, parser_hook: ProtocolParser) -> None:
        """
        Basic constructor.

        :param parser_hook:
        """
        # init all hornet stuff using new class - will change to autodetect someday:
        # self.currentAChook = FA18Handler(self, parserHook)

        self.bufferAC = StringBuffer(parser_hook, 0x0000, 16, lambda v: self.set_ac(v))
        self.parser = parser_hook
        self.currentAC = ''
        self.currentACHook = None
        self.shouldActivateNewAC = False

        self.isAlreadyPressed = False

        # display parameters
        self.width = 160
        self.height = 43

        # GLCD Init
        arch = 'x64' if all([architecture()[0] == '64bit', maxsize > 2 ** 32, sizeof(c_voidp) > 4]) else 'x86'
        dll = "C:\\Program Files\\Logitech Gaming Software\\LCDSDK_8.57.148\\Lib\\GameEnginesWrapper\\{}\\LogitechLcdEnginesWrapper.dll".format(arch)
        GLCD_SDK.init_dll(dll)
        GLCD_SDK.LogiLcdInit('Python', GLCD_SDK.TYPE_MONO)

        self.img = Image.new('1', (self.width, self.height), 0)
        self.draw = ImageDraw.Draw(self.img)
        self.font1 = ImageFont.truetype('consola.ttf', 11)
        self.font2 = ImageFont.truetype('consola.ttf', 16)

    # for new A/C implementation, make sure that setAC() makes shouldActivateNewAC=true, and then activateNewAC creates needed handler###
    def set_ac(self, value: str) -> None:
        """
        Set aircraft.

        :param value:
        """
        if not value == self.currentAC:
            self.currentAC = value
            if value == "NONE":
                print("Unknown AC data: ", value, )
                self.info_display(("Unknown AC data:", self.currentAC))

            elif value == "FA-18C_hornet":
                self.info_display()
                print("Detected AC: ", value)
                self.shouldActivateNewAC = True

            elif value == "AV8BNA":
                print("Detected AC: ", value)
                self.shouldActivateNewAC = True

            elif value == "F-16C_50":
                print("Detected AC: ", value)
                self.shouldActivateNewAC = True

            else:
                # FIXME a może tylko tyo zostawić, żeby po prostu zaczynał aktywaować nowy moduł, a weryfikację zostawić w metodzie poniżej?
                print("Unknown AC data: ", value)
                self.info_display(("Unknown AC data:", self.currentAC))

    def activate_new_ac(self) -> None:
        """Actiate new aircraft."""
        self.shouldActivateNewAC = False
        if self.currentAC == "FA-18C_hornet":
            self.currentACHook = FA18Handler(self, self.parser)
        elif self.currentAC == "AV8BNA":
            self.info_display(("AV8BNA", "not implemented yet"))
        elif self.currentAC == "F-16C_50":
            self.currentACHook = F16Handler(self, self.parser)

    def info_display(self, message=('', '')) -> None:
        """
        Send message to display.

        :param message:
        """
        # clear bitmap
        self.draw.rectangle((0, 0, self.width, self.height), 0, 0)
        # self.ClearDisplay()

        if message == ('', ''):
            self.draw.text((0, 0), self.currentAC, 1, self.font1)
        else:
            y = 0
            # self.draw.text((0,0), message, 1, self.font1)
            for line in message:
                self.draw.text((0, y), line, 1, self.font1)
                y = y + 10

        pixels = list(self.img.getdata())
        for i in range(0, len(pixels)):
            pixels[i] *= 128

        self.update_display(pixels)
        # if GLCD_SDK.LogiLcdIsConnected(GLCD_SDK.TYPE_MONO):
        #     GLCD_SDK.LogiLcdMonoSetBackground((c_ubyte * (self.width *self.height))(*pixels))
        #     GLCD_SDK.LogiLcdUpdate()
        # else:
        #     print("LCD is not connected")

    def update_display(self, pixels: List[c_ubyte]) -> None:
        """
        Update display.

        :param pixels:
        """
        # put bitmap array into display
        if GLCD_SDK.LogiLcdIsConnected(GLCD_SDK.TYPE_MONO):
            GLCD_SDK.LogiLcdMonoSetBackground((c_ubyte * (self.width * self.height))(*pixels))
            GLCD_SDK.LogiLcdUpdate()
        else:
            print("LCD is not connected")

    def clear_display(self, true_clear=False) -> None:
        """
        Clear display.

        :param true_clear:
        """
        GLCD_SDK.LogiLcdMonoSetBackground((c_ubyte * (self.width * self.height))(*[0] * (self.width * self.height)))
        if true_clear:
            for i in range(4):
                GLCD_SDK.LogiLcdMonoSetText(i, "")
        GLCD_SDK.LogiLcdUpdate()

    def check_buttons(self) -> int:
        """
        Check button state.

        :return:
        """
        if GLCD_SDK.LogiLcdIsButtonPressed(GLCD_SDK.MONO_BUTTON_0):
            if not self.isAlreadyPressed:
                self.isAlreadyPressed = True
                return 1
            else:
                return 0

        elif GLCD_SDK.LogiLcdIsButtonPressed(GLCD_SDK.MONO_BUTTON_1):
            if not self.isAlreadyPressed:
                self.isAlreadyPressed = True
                return 2
            else:
                return 0

        elif GLCD_SDK.LogiLcdIsButtonPressed(GLCD_SDK.MONO_BUTTON_2):
            if not self.isAlreadyPressed:
                self.isAlreadyPressed = True
                return 3
            else:
                return 0

        elif GLCD_SDK.LogiLcdIsButtonPressed(GLCD_SDK.MONO_BUTTON_3):
            if not self.isAlreadyPressed:
                self.isAlreadyPressed = True
                return 4
            else:
                return 0
        else:
            self.isAlreadyPressed = False
            return 0

    def button_handle(self, s: socket) -> None:
        """
        Button handler.

        :param s:
        """
        button = self.check_buttons()
        if not button == 0:
            s.send(bytes(self.currentACHook.button_handle_specific_ac(button), "utf-8"))
