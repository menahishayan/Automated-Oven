import asyncio
from busio import SPI
from digitalio import DigitalInOut
from pwmio import PWMOut
from board import SCK, MOSI, MISO, CE0, D24, D25, D22

from adafruit_rgb_display.st7789 import ST7789
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from PIL.ImageOps import invert
from aggdraw import Draw, Pen, Brush
from time import time
from math import floor
from random import sample

class DisplayContent:
    def __init__(self, CS_PIN=CE0, DC_PIN=D24, RESET_PIN=D25):
        self.CS_PIN = CS_PIN
        self.DC_PIN = DC_PIN
        self.RESET_PIN = RESET_PIN

    async def init(self, e=None):
        self.e = e

        spi = SPI(clock=SCK, MOSI=MOSI, MISO=MISO)

        self.disp = ST7789(
            spi,
            rotation=270,
            width=128,
            height=160,
            x_offset=0,
            y_offset=0,
            baudrate=24000000,
            cs=DigitalInOut(self.CS_PIN),
            dc=DigitalInOut(self.DC_PIN),
            rst=DigitalInOut(self.RESET_PIN))

        if self.disp.rotation % 180 == 90:
            self.height = self.disp.width
            self.width = self.disp.height
        else:
            self.width = self.disp.width
            self.height = self.disp.height

        self.backlight = PWMOut(D22, frequency=1000, duty_cycle=0)

        self.clear()
        await self.setBacklight(50)

        self.fonts = {
            'timer': ImageFont.truetype('./fonts/SF-Compact-Display-Medium.ttf', 36),
            'subtitle': ImageFont.truetype('./fonts/SF-Pro-Display-Regular.ttf', 16),
            'alert': ImageFont.truetype('./fonts/SF-Pro-Display-Semibold.ttf', 28),
            'prompt': ImageFont.truetype('./fonts/SF-Pro-Display-Semibold.ttf', 20),
            'mini': ImageFont.truetype('./fonts/SF-Pro-Display-Semibold.ttf', 14),
        }

        self.colors = {
            'preheat': '#ff7300',
            'cook': '#ffd600',
            'notify': '#634dd3',
            'checkpoint': '#3f91ff',
            'red': '#e93838',
            'cool': '#f3fbff',
        }
    
    def clear(self):
        image = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, self.width, self.height), outline="#fff", fill="#fff")
        self.disp.image(image)

    def display(self, image):
        image = ImageEnhance.Color(image).enhance(3.5)
        # image = ImageEnhance.Contrast(image).enhance(0.9)
        # image = ImageEnhance.Brightness(image).enhance(0.4)
        image = invert(image)
        self.disp.image(image)

    async def path(self, path):
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

        self.display(image)

    async def text(self, text):
        image = Image.new("RGB", (self.width, self.height))

        draw = ImageDraw.Draw(image)

        draw.rectangle((0, 0, self.width, self.height), fill="#fff")

        text = text.capitalize()
        w, h = draw.textsize(text, font=self.fonts['prompt'])
        draw.text(((self.width-w)/2, (self.height-h)/2), text,
                  font=self.fonts['prompt'], align="center", fill="#000")

        self.disp.image(image)

    async def alert(self, text):
        image = Image.new("RGB", (self.width, self.height))

        draw = ImageDraw.Draw(image)

        draw.rectangle((0, 0, self.width, self.height), fill="#fff")

        text = text.capitalize()
        w, h = draw.textsize(text, font=self.fonts['alert'])
        draw.text(((self.width-w)/2, (self.height-h)/2), text,
                  font=self.fonts['alert'], align="center", fill="#000")

        self.display(image)

    async def _progress(self, percent):
        image = Image.new("RGB", (self.width, 12))

        draw = ImageDraw.Draw(image)

        draw.pieslice([(3, 3), (11, 11)], start=90, end=270, fill="#fff", outline="#fff")
        draw.rectangle((5, 3, int((percent * (self.width-8)) / 100)+5, 11), outline="#fff", fill="#fff")

        image = invert(image)
        return image

    async def circleProgress(self, percent, text=""):
        image = Image.new("RGB", (self.width, self.height))

        draw = Draw(image)
        pen = Pen("white", 7)

        radian = percent * 3.6
        draw.arc((50, 34, 110, 94), 450-radian, 90, pen)

        draw.flush()
        imDraw = ImageDraw.Draw(image)

        if len(text) > 0:
            text = text.capitalize()
            w, h = imDraw.textsize(text, font=self.fonts['prompt'])
            imDraw.text(((self.width-w)/2, (self.height-h)/2),
                        text, font=self.fonts['prompt'], align="center", fill="#fff")

        image = invert(image)
        self.display(image)

    async def loading(self):
        image = Image.new("RGB", (self.width, self.height))

        draw = Draw(image)

        colors = list(self.colors.values())
        draw.ellipse((50, 59, 60, 69), Pen(colors[0]), Brush(colors[0]))
        draw.ellipse((75, 59, 85, 69), Pen(colors[1]), Brush(colors[1]))
        draw.ellipse((100, 59, 110, 69), Pen(colors[2]), Brush(colors[2]))

        draw.flush()

        self.display(image)


    # async def cookingListener(self):
    #     while not self.e._SIGKILL:
    #         if self.e.cook.isCooking:
    #             await self.e.dispatch([[self.cooking]])
    #         else:
    #             await asyncio.sleep(1)

    def getProgressItems(self,curStepIndex, steps):
        total = len(steps)
        marginTop = 4
        dia = 9
        space = 12

        image = Image.new("RGB", (self.width, dia+int(marginTop*1.5)))
        draw = Draw(image)

        w = ((dia + space) * total) - space
        marginLeft = (self.width - w)/2
        
        for s in range(total):
            left = marginLeft + ((dia+space)*s)
            draw.ellipse((left, marginTop, left+dia, marginTop+dia), Pen(self.colors[steps[s]]), Brush(self.colors[steps[s]]))
            if curStepIndex < s:
                draw.ellipse((left+ (dia*0.25), marginTop + (dia*0.25), left+(dia*0.75), marginTop+(dia*0.75)), Pen("#000"), Brush("#000"))
        draw.flush()

        return image

    async def preheat(self,curStepIndex,steps):
        try:
            while not self.e._SIGKILL and not self.e.cook.SIGTERM:
                if steps[curStepIndex]['isDone']:
                    break
                image = Image.new("RGB",(self.width,self.height))

                imDraw = ImageDraw.Draw(image)
                image.paste(Image.open('./images/PreheatScreen.jpg'))

                image.paste(self.getProgressItems(curStepIndex,[s['type'] for s in steps]))

                textMain = '{:.1f}'.format(self.e.cook.topRod.get())
                textSub = 'Preheat'
                w_s, h_s = imDraw.textsize(textSub, font=self.fonts['mini'])
                imDraw.text((73, 45), textMain, font=self.fonts['alert'], align="right", fill="#fff")
                imDraw.text(((self.width-w_s)/2, 102), textSub, font=self.fonts['mini'], align="center", fill="#fff")

                self.display(image)
                await asyncio.sleep(1)
        except Exception as e:
            self.e.err(e)

    # async def cooking(self):
    #     image = Image.new("RGB", (self.width, self.height))

    #     imDraw = ImageDraw.Draw(image)

    #     item = self.e.cook.item
    #     end = self.e.cook.endTime
    #     start = self.e.cook.startTime
    #     top, bottom = '0','0'

    #     while floor(end-time()) > 0:
    #         if self.e._SIGKILL:
    #             break
    #         imDraw.rectangle((0, 0, self.width, self.height), fill="#fff")

    #         if not top == '0' and not bottom == '0':
    #             if not top == str(self.e.cook.top):
    #                 await self.alert(str(self.e.cook.top))
    #                 await asyncio.sleep(1)
    #             elif not bottom == str(self.e.cook.bottom):
    #                 await self.alert(str(self.e.cook.bottom))
    #                 await asyncio.sleep(1)


    #         # Top
    #         top = str(self.e.cook.top)
    #         imDraw.text((2, 16), top, font=self.fonts['subtitle'], align="center", fill="#000")

    #         # Bottom
    #         bottom = str(self.e.cook.bottom)
    #         w_mini, _ = imDraw.textsize(bottom, font=self.fonts['subtitle'])
    #         imDraw.text((self.width-w_mini-2, 16), bottom, font=self.fonts['subtitle'], align="center", fill="#000")

    #         # Measured
    #         # try:
    #         #     overalltemp = str(self.e.temp)
    #         #     w_mini, _ = imDraw.textsize(overalltemp, font=self.fonts['subtitle'])
    #         #     imDraw.text(((self.width-w_mini)/2, 16), overalltemp, font=self.fonts['subtitle'], align="center", fill="#000")
    #         # except Exception as e:
    #         #     self.e.err("error: " + e)

    #         if self.e.cook.isPaused == True:
    #             await self.path('./images/PauseScreen.jpg')
    #         else:
    #             end = self.e.cook.endTime

    #             image.paste(await self._progress(((time() - start) / (end - start))*100))
    #             textMain = '{:02d}:{:02d}'.format(
    #                 floor((end-time())/60), int(end-time()) % 60)
    #             textSub = '{}'.format(item)
    #             w_m, h_m = imDraw.textsize(textMain, font=self.fonts['timer'])
    #             w_s, h_s = imDraw.textsize(textSub, font=self.fonts['subtitle'])

    #             imDraw.text(((self.width-w_m)/2, (self.height-h_m)/2), textMain, font=self.fonts['timer'], align="center", fill="#000")
    #             imDraw.text(((self.width-w_s)/2, ((self.height-h_s)/2)+h_m+1), textSub, font=self.fonts['subtitle'], align="center", fill="#000")


    #             self.disp.image(image)
    #         await asyncio.sleep(1)

    #     # self.e.cook.done()
     
    #     if self.e._SIGKILL:
    #         await self.path('./images/PowerScreen.jpg')
    #     else:
    #         await self.path('./images/DoneScreen.jpg')

    async def setBacklight(self, percent):
        self.backlight.duty_cycle = int(65535 * percent / 100)
        return True

    async def getBacklight(self):
        return int((self.backlight.duty_cycle * 100) / 65535)
