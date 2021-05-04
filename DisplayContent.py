import busio
import digitalio
import pwmio
from board import SCK, MOSI, MISO, CE0, D24, D25, D22

from adafruit_rgb_display.st7789 import ST7789
from PIL import Image, ImageDraw, ImageFont
import PIL.ImageOps  
import aggdraw

class DisplayContent:
    def __init__(self, CS_PIN=CE0, DC_PIN=D24, RESET_PIN=D25):
        self.CS_PIN = CS_PIN
        self.DC_PIN = DC_PIN
        self.RESET_PIN = RESET_PIN

        spi = busio.SPI(clock=SCK, MOSI=MOSI, MISO=MISO)

        self.disp = ST7789(
            spi,
            rotation=270,
            width=128,
            height=160,
            x_offset=0,
            y_offset=0,
            baudrate=24000000,
            cs=digitalio.DigitalInOut(CS_PIN),
            dc=digitalio.DigitalInOut(DC_PIN),
            rst=digitalio.DigitalInOut(RESET_PIN))

        if self.disp.rotation % 180 == 90:
            self.height = self.disp.width
            self.width = self.disp.height
        else:
            self.width = self.disp.width 
            self.height = self.disp.height

        self.backlight = pwmio.PWMOut(D22, frequency=1000, duty_cycle=32767)

        image = Image.new("RGB", (self.width, self.height))

        draw = ImageDraw.Draw(image)

        draw.rectangle((0, 0, self.width, self.height), outline=0, fill=(0, 0, 0))

        image = PIL.ImageOps.invert(image)
        self.disp.image(image)

    def path(self, path):
        image = Image.open(path)

        image_ratio = image.width / image.height
        screen_ratio = self.width / self.height
        if screen_ratio < image_ratio:
            scaled_width = image.width * self.height // image.height
            scaled_height = self.height
        else:
            scaled_width = self.width
            scaled_height = image.height * self.width // image.width
        image = image.resize((scaled_width, scaled_height), Image.BICUBIC)

        x = scaled_width // 2 - self.width // 2
        y = scaled_height // 2 - self.height // 2
        image = image.crop((x, y, x + self.width, y + self.height))

        image = PIL.ImageOps.invert(image)
        self.disp.image(image)

    def image(self, image):
        self.disp.image(image)

    def text(self, text):
        image = Image.new("RGB", (self.width, self.height))

        draw = ImageDraw.Draw(image)

        draw.rectangle((0, 0, self.width, self.height), outline=0, fill="#000")

        text = text.capitalize() 
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18) 
        w, h = draw.textsize(text, font=font)
        draw.text(((self.width-w)/2,(self.height-h)/2), text, font = font, align ="center", fill="#fff") 

        image = PIL.ImageOps.invert(image)
        self.disp.image(image)

    def progress(self,percent, text=""):
        image = Image.new("RGB", (self.width, self.height))

        draw = ImageDraw.Draw(image)

        draw.rectangle((0, 0, self.width, self.height), outline=0, fill="#000")
        draw.rectangle((0, 0, int((percent * self.width)/ 100), 14), outline=0, fill="#fff")

        if len(text) > 0:
            text = text.capitalize() 
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18) 
            w, h = draw.textsize(text, font=font)
            draw.text(((self.width-w)/2,(self.height-h)/2), text, font = font, align ="center", fill="#fff") 

        image = PIL.ImageOps.invert(image)
        self.disp.image(image)

    def circleProgress(self,percent, text=""):
        image = Image.new("RGB", (self.width, self.height))

        draw = aggdraw.Draw(image)
        pen = aggdraw.Pen("white", 7)

        radian = percent* 3.6
        draw.arc((50, 34, 110, 94), 450-radian, 90,pen)

        draw.flush()
        imDraw = ImageDraw.Draw(image)

        if len(text) > 0:
            text = text.capitalize() 
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18) 
            w, h = imDraw.textsize(text, font=font)
            imDraw.text(((self.width-w)/2,(self.height-h)/2), text, font = font, align ="center", fill="#fff") 

        image = PIL.ImageOps.invert(image)
        self.disp.image(image)

    def loading(self):
        image = Image.new("RGB", (self.width, self.height))

        draw = aggdraw.Draw(image)
        pen = aggdraw.Pen("white")
        brush = aggdraw.Brush("white")

        draw.ellipse((50, 59, 60, 69),pen,brush)
        draw.ellipse((75, 59, 85, 69),pen,brush)
        draw.ellipse((100, 59, 110, 69),pen,brush)

        draw.flush()
        # imDraw = ImageDraw.Draw(image)

        # if len(text) > 0:
        #     text = text.capitalize() 
        #     font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18) 
        #     w, h = imDraw.textsize(text, font=font)
        #     imDraw.text(((self.width-w)/2,(self.height-h)/2), text, font = font, align ="center", fill="#fff") 

        image = PIL.ImageOps.invert(image)
        self.disp.image(image)

    def setBacklight(self, percent):
        self.backlight.duty_cycle = int(65535 * percent / 100)

    def getBacklight(self):
        return int((self.backlight.duty_cycle * 100) / 65535)