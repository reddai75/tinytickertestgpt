# *****************************************************************************
# * | File        :	  epd2in13.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V4.0
# * | Date        :   2019-06-20
# # | Info        :   python demo
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


import logging

from ._base import EPDMonochrome
from .epdconfig import CONFIG

# Display resolution
EPD_WIDTH = 122
EPD_HEIGHT = 250

logger = logging.getLogger(__name__)


class EPD(EPDMonochrome):
    def __init__(self):
        self.reset_pin = CONFIG.RST_PIN
        self.dc_pin = CONFIG.DC_PIN
        self.busy_pin = CONFIG.BUSY_PIN
        self.cs_pin = CONFIG.CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

    lut_full_update = [
        0x22,
        0x55,
        0xAA,
        0x55,
        0xAA,
        0x55,
        0xAA,
        0x11,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x1E,
        0x1E,
        0x1E,
        0x1E,
        0x1E,
        0x1E,
        0x1E,
        0x1E,
        0x01,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
    ]

    lut_partial_update = [
        0x18,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x0F,
        0x01,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
    ]

    # Hardware reset
    def reset(self):
        CONFIG.digital_write(self.reset_pin, 1)
        CONFIG.delay_ms(200)
        CONFIG.digital_write(self.reset_pin, 0)
        CONFIG.delay_ms(5)
        CONFIG.digital_write(self.reset_pin, 1)
        CONFIG.delay_ms(200)

    def send_command(self, command):
        CONFIG.digital_write(self.dc_pin, 0)
        CONFIG.digital_write(self.cs_pin, 0)
        CONFIG.spi_writebyte([command])
        CONFIG.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        CONFIG.digital_write(self.dc_pin, 1)
        CONFIG.digital_write(self.cs_pin, 0)
        CONFIG.spi_writebyte([data])
        CONFIG.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        while CONFIG.digital_read(self.busy_pin) == 1:  # 0: idle, 1: busy
            CONFIG.delay_ms(100)

    def TurnOnDisplay(self):
        self.send_command(0x22)  # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0xC4)
        self.send_command(0x20)  # MASTER_ACTIVATION
        self.send_command(0xFF)  # TERMINATE_FRAME_READ_WRITE

        logger.debug("e-Paper busy")
        self.ReadBusy()
        logger.debug("e-Paper busy release")

    def init(self):
        if CONFIG.module_init() != 0:
            return -1
        # EPD hardware init start
        self.reset()
        self.send_command(0x01)  # DRIVER_OUTPUT_CONTROL
        self.send_data((EPD_HEIGHT - 1) & 0xFF)
        self.send_data(((EPD_HEIGHT - 1) >> 8) & 0xFF)
        self.send_data(0x00)  # GD = 0 SM = 0 TB = 0

        self.send_command(0x0C)  # BOOSTER_SOFT_START_CONTROL
        self.send_data(0xD7)
        self.send_data(0xD6)
        self.send_data(0x9D)

        self.send_command(0x2C)  # WRITE_VCOM_REGISTER
        self.send_data(0xA8)  # VCOM 7C

        self.send_command(0x3A)  # SET_DUMMY_LINE_PERIOD
        self.send_data(0x1A)  # 4 dummy lines per gate

        self.send_command(0x3B)  # SET_GATE_TIME
        self.send_data(0x08)  # 2us per line

        self.send_command(0x3C)  # BORDER_WAVEFORM_CONTROL
        self.send_data(0x03)

        self.send_command(0x11)  # DATA_ENTRY_MODE_SETTING
        self.send_data(0x03)  # X increment; Y increment

        # WRITE_LUT_REGISTER
        self.send_command(0x32)
        for count in range(30):
            self.send_data(self.lut_full_update[count])

        return 0

    ##
    #  @brief: specify the memory area for data R/W
    ##
    def SetWindows(self, x_start, y_start, x_end, y_end):
        self.send_command(0x44)  # SET_RAM_X_ADDRESS_START_END_POSITION
        self.send_data((x_start >> 3) & 0xFF)
        self.send_data((x_end >> 3) & 0xFF)
        self.send_command(0x45)  # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        self.send_data(y_end & 0xFF)
        self.send_data((y_end >> 8) & 0xFF)

    ##
    #  @brief: specify the start point for data R/W
    ##
    def SetCursor(self, x, y):
        self.send_command(0x4E)  # SET_RAM_X_ADDRESS_COUNTER
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data((x >> 3) & 0xFF)
        self.send_command(0x4F)  # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)
        self.ReadBusy()

    def getbuffer(self, image):
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        buf = [0xFF] * (linewidth * self.height)
        image_monocolor = image.convert("1")
        imwidth, imheight = image_monocolor.size

        if imwidth == self.width and imheight == self.height:
            logger.debug("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    if image_monocolor.getpixel((x, y)) == 0:
                        # x = imwidth - x
                        buf[int(x / 8) + y * linewidth] &= ~(0x80 >> (x % 8))
        elif imwidth == self.height and imheight == self.width:
            logger.debug("Horizontal")
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1
                    if image_monocolor.getpixel((x, y)) == 0:
                        # newy = imwidth - newy - 1
                        buf[int(newx / 8) + newy * linewidth] &= ~(0x80 >> (y % 8))
        return bytearray(buf)

    def display(self, image):
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self.SetWindows(0, 0, self.width, self.height)
        for j in range(0, self.height):
            self.SetCursor(0, j)
            self.send_command(0x24)
            for i in range(0, linewidth):
                self.send_data(image[i + j * linewidth])
        self.TurnOnDisplay()

    def Clear(self, color=0xFF):
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self.SetWindows(0, 0, self.width, self.height)
        for j in range(0, self.height):
            self.SetCursor(0, j)
            self.send_command(0x24)
            for _ in range(0, linewidth):
                self.send_data(color)
        self.TurnOnDisplay()

    def sleep(self):
        self.send_command(0x10)  # enter deep sleep
        self.send_data(0x01)
        CONFIG.delay_ms(100)

        CONFIG.delay_ms(2000)
        CONFIG.module_exit()
