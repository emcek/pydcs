from ctypes import c_ubyte, sizeof, c_void_p
from logging import basicConfig, DEBUG, info, debug, warning
from math import log2
from platform import architecture
from socket import socket
from sys import maxsize
from typing import List

from PIL import Image, ImageFont, ImageDraw

import lcd_sdk
from aircrafts import FA18Handler, F16Handler
from dcsbios import StringBuffer, ProtocolParser

basicConfig(format='%(asctime)s | %(levelname)-6s | %(message)s / %(filename)s:%(lineno)d', level=DEBUG)


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
        self.width = lcd_sdk.MONO_WIDTH
        self.height = lcd_sdk.MONO_HEIGHT

        # GLCD Init
        arch = 'x64' if all([architecture()[0] == '64bit', maxsize > 2 ** 32, sizeof(c_void_p) > 4]) else 'x86'
        dll = f"C:\\Program Files\\Logitech Gaming Software\\LCDSDK_8.57.148\\Lib\\GameEnginesWrapper\\{arch}\\LogitechLcdEnginesWrapper.dll"
        lcd_sdk.init_dll(dll)
        lcd_sdk.LogiLcdInit('Python', lcd_sdk.TYPE_MONO)

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
            if value in ('FA-18C_hornet', 'AV8BNA', 'F-16C_50'):
                info(f'Detected AC: {value}')
                self.info_display()
                self.shouldActivateNewAC = True
            else:
                # FIXME a może tylko tyo zostawić, żeby po prostu zaczynał aktywaować nowy moduł, a weryfikację zostawić w metodzie poniżej?
                warning(f'Unknown AC data: {value}')
                self.info_display(('Unknown AC data:', self.currentAC))

    def activate_new_ac(self) -> None:
        """Actiate new aircraft."""
        self.shouldActivateNewAC = False
        if self.currentAC == 'FA-18C_hornet':
            self.currentACHook = FA18Handler(self, self.parser)
        elif self.currentAC == 'AV8BNA':
            self.info_display(('AV8BNA', 'not implemented yet'))
        elif self.currentAC == 'F-16C_50':
            self.currentACHook = F16Handler(self, self.parser)
        debug(f'Current AC: {self.currentAC} {self.currentACHook}')

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
        for i, _ in enumerate(pixels):
            pixels[i] *= 128

        self.update_display(pixels)

    def update_display(self, pixels: List[c_ubyte]) -> None:
        """
        Update display.

        :param pixels:
        """
        # put bitmap array into display
        if lcd_sdk.LogiLcdIsConnected(lcd_sdk.TYPE_MONO):
            lcd_sdk.LogiLcdMonoSetBackground((c_ubyte * (self.width * self.height))(*pixels))
            lcd_sdk.LogiLcdUpdate()
        else:
            warning('LCD is not connected')

    def clear_display(self, true_clear=False) -> None:
        """
        Clear display.

        :param true_clear:
        """
        lcd_sdk.LogiLcdMonoSetBackground((c_ubyte * (self.width * self.height))(*[0] * (self.width * self.height)))
        if true_clear:
            for i in range(4):
                lcd_sdk.LogiLcdMonoSetText(i, '')
        lcd_sdk.LogiLcdUpdate()

    def check_buttons(self) -> int:
        """
        Check button state.

        :return:
        """
        for btn in (lcd_sdk.MONO_BUTTON_0, lcd_sdk.MONO_BUTTON_1, lcd_sdk.MONO_BUTTON_2, lcd_sdk.MONO_BUTTON_3):
            if lcd_sdk.LogiLcdIsButtonPressed(btn):
                if not self.isAlreadyPressed:
                    self.isAlreadyPressed = True
                    return int(log2(btn)) + 1
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
        if button:
            s.send(bytes(self.currentACHook.button_handle_specific_ac(button), 'utf-8'))
