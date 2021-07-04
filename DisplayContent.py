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

        self.backlight = PWMOut(D22, frequency=2000, duty_cycle=0)

        self.clear()
        await self.setBacklight(await self.e.config.get('backlight'))

        self.fonts = {
            'timer': ImageFont.truetype('./fonts/SF-Compact-Display-Medium.ttf', 36),
            'subtitle': ImageFont.truetype('./fonts/SF-Pro-Display-Regular.ttf', 16),
            'alert': ImageFont.truetype('./fonts/SF-Pro-Display-Semibold.ttf', 28),
            'prompt': ImageFont.truetype('./fonts/SF-Pro-Display-Semibold.ttf', 20),
            'mini': ImageFont.truetype('./fonts/SF-Pro-Display-Semibold.ttf', 13),
        }

        self.colors = {
            'preheat': '#ff7300',
            'cook': '#ffd600',
            'notify': '#634dd3',
            'checkpoint': '#3f91ff',
            'poweroff': '#e93838',
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

    def icon(self, path, large=False):
        image = Image.open(path)
        return image.resize((50, 50), Image.BICUBIC) if large else image.resize((30, 30), Image.BICUBIC)

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

    def circleProgressLeft(self, percent, color):
        dia = 44

        image = Image.new("RGB", (dia+6, dia+6))

        draw = Draw(image)
        pen = Pen(self.colors[color], 6)

        radian = percent * 360
        draw.arc((3, 3, dia+3, dia+3), 450-radian, 90, pen)

        draw.flush()

        return image

    def getProgressItems(self, curStepIndex, steps):
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
                draw.ellipse((left + (dia*0.25), marginTop + (dia*0.25), left+(dia*0.75), marginTop+(dia*0.75)), Pen("#000"), Brush("#000"))
        draw.flush()

        return image

    def baseImageLeftIcon(self, curStepIndex, stepTypes, textMain, percent, subtitle=None):
        image = Image.new("RGB", (self.width, self.height))

        imDraw = ImageDraw.Draw(image)

        name = stepTypes[curStepIndex].capitalize()

        image.paste(self.getProgressItems(curStepIndex, stepTypes))
        image.paste(self.circleProgressLeft(percent, stepTypes[curStepIndex]), (14, (self.height-50)//2))
        icon = self.icon('./images/{}Icon.png'.format(name))
        image.paste(icon, (24, (self.height-30)//2), mask=icon)

        textSub = subtitle if subtitle else name
        w_m, _ = imDraw.textsize(textMain, font=self.fonts['alert'])
        w_s, _ = imDraw.textsize(textSub, font=self.fonts['mini'])
        imDraw.text((self.width-w_m-16, 45), textMain, font=self.fonts['alert'], align="right", fill="#fff")
        imDraw.text(((self.width-w_s)/2, 102), textSub, font=self.fonts['mini'], align="center", fill="#fff")

        return image

    def baseImageCenterIcon(self, curStepIndex, stepTypes, customIcon=None, customText=None):
        image = Image.new("RGB", (self.width, self.height))

        imDraw = ImageDraw.Draw(image)

        name = ""
        if curStepIndex > -1:
            name = stepTypes[curStepIndex].capitalize()
            image.paste(self.getProgressItems(curStepIndex, stepTypes))
            
        icon = self.icon('./images/{}Icon.png'.format(customIcon if customIcon else name), large=True)
        image.paste(icon, ((self.width-50)//2, (self.height-50)//2), mask=icon)

        textSub = customText if customText else name
        w_s, _ = imDraw.textsize(textSub, font=self.fonts['mini'])
        imDraw.text(((self.width-w_s)/2, 102), textSub, font=self.fonts['mini'], align="center", fill="#fff")

        return image

    async def preheat(self, curStepIndex, steps):
        try:
            # self.clear()

            ht = round(self.e.cook.rod.heatingTime(steps[curStepIndex]['temp']))
            while not self.e._SIGKILL and not self.e.cook.SIGTERM and not self.e.cook.SIGPAUSE:
                if steps[curStepIndex]['isDone']:
                    break
                image = Image.new("RGB", (self.width, self.height))
                imDraw = ImageDraw.Draw(image)

                currTemp = self.e.cook.rod.get()
                percent = 0

                if 'endTime' not in steps[curStepIndex]:
                    steps[curStepIndex]['endTime'] = steps[curStepIndex]['startTime'] + (ht if ht >= 0 else self.e.cook.rod.coolingTime(steps[curStepIndex]['temp']))

                if 'startTime' in steps[curStepIndex] and 'endTime' in steps[curStepIndex]:
                    try:
                        n = time()-steps[curStepIndex]['startTime']
                        d = steps[curStepIndex]['endTime']-steps[curStepIndex]['startTime']
                        percent = round(n/d,2)
                        if percent > 1:
                            break
                    except Exception:
                        break

                image.paste(
                    self.baseImageLeftIcon(
                        curStepIndex,
                        [s['type'] for s in steps],
                        str(currTemp),
                        percent
                    )
                )

                imDraw.line((144-(currTemp*60/250), 44, 144, 44), fill="#fff", width=3)

                finalTemp = int(steps[curStepIndex]['temp'])
                w_s, _ = imDraw.textsize(str(finalTemp), font=self.fonts['mini'])
                imDraw.text((self.width-w_s-16, 27), str(finalTemp), font=self.fonts['mini'], align="right", fill="#fff")

                self.display(image)
                await asyncio.sleep(0.3)
        except Exception as e:
            self.e.err(e)

    async def cook(self, curStepIndex, steps):
        try:
            self.clear()
            while not self.e._SIGKILL and not self.e.cook.SIGTERM and not self.e.cook.SIGPAUSE:
                if steps[curStepIndex]['isDone']:
                    break
                image = Image.new("RGB", (self.width, self.height))
                imDraw = ImageDraw.Draw(image)

                percent = 0
                timeRemaining = steps[curStepIndex]['duration'] * (2 if self.e.config._get('demoMode') else 60)

                if 'startTime' in steps[curStepIndex] and 'endTime' in steps[curStepIndex]:
                    try:
                        n = time()-steps[curStepIndex]['startTime']
                        d = steps[curStepIndex]['endTime']-steps[curStepIndex]['startTime']
                        percent = round(n/d,2)
                        if percent > 1:
                            break
                        timeRemaining = int(steps[curStepIndex]['endTime'] - time())
                    except Exception:
                        break

                image.paste(
                    self.baseImageLeftIcon(
                        curStepIndex,
                        [s['type'] for s in steps],
                        '{:02d}:{:02d}'.format(timeRemaining//60, timeRemaining % 60),
                        percent,
                        self.e.cook.item
                    )
                )

                topTemp = int(steps[curStepIndex]['topTemp'])
                imDraw.line((144-(topTemp*60/250), 44, 144, 44), fill="#fff", width=3)
                w_t, _ = imDraw.textsize(str(topTemp), font=self.fonts['mini'])
                imDraw.text((self.width-w_t-16, 27), str(topTemp), font=self.fonts['mini'], align="right", fill="#fff")


                bottomTemp = int(steps[curStepIndex]['bottomTemp'])
                imDraw.line((144-(bottomTemp*60/250), 78, 144, 78), fill="#fff", width=3)
                w_b, _ = imDraw.textsize(str(bottomTemp), font=self.fonts['mini'])
                imDraw.text((self.width-w_b-16, 80), str(bottomTemp), font=self.fonts['mini'], align="right", fill="#fff")

                self.display(image)
                await asyncio.sleep(0.3)
        except Exception as e:
            self.e.err(e)

    async def notify(self, curStepIndex, steps):
        try:
            # self.clear()
            while not self.e._SIGKILL and not self.e.cook.SIGTERM and not self.e.cook.SIGPAUSE:
                if steps[curStepIndex]['endTime'] <= time():
                    break
                image = Image.new("RGB", (self.width, self.height))
                
                image.paste(
                    self.baseImageCenterIcon(
                        curStepIndex,
                        [s['type'] for s in steps]
                    )
                )

                self.display(image)
                await asyncio.sleep(0.5)
        except Exception as e:
            self.e.err(e)

    async def checkpoint(self, curStepIndex, steps):
        try:
            # self.clear()
            while not self.e._SIGKILL and not self.e.cook.SIGTERM and not self.e.cook.SIGPAUSE:
                if steps[curStepIndex]['endTime'] <= time():
                    break
                image = Image.new("RGB", (self.width, self.height))
                
                image.paste(
                    self.baseImageCenterIcon(
                        curStepIndex,
                        [s['type'] for s in steps]
                    )
                )

                self.display(image)
                await asyncio.sleep(0.5)
        except Exception as e:
            self.e.err(e)

    async def cool(self, curStepIndex, steps):
        try:
            # self.clear()
            while not self.e._SIGKILL and not self.e.cook.SIGTERM:
                if steps[curStepIndex]['endTime'] <= time():
                    break
                image = Image.new("RGB", (self.width, self.height))
                
                image.paste(
                    self.baseImageCenterIcon(
                        curStepIndex,
                        [s['type'] for s in steps]
                    )
                )

                self.display(image)
                await asyncio.sleep(0.5)
        except Exception as e:
            self.e.err(e)

    async def pause(self,curStepIndex,stepTypes):
        self.clear()
        image = Image.new("RGB", (self.width, self.height))
        image.paste(
            self.baseImageCenterIcon(
                curStepIndex,
                stepTypes,
                "Pause",
                "Paused"
            )
        )
        self.display(image)

    async def poweroff(self,curStepIndex,stepTypes):
        image = Image.new("RGB", (self.width, self.height))
        image.paste(
            self.baseImageCenterIcon(
                curStepIndex,
                stepTypes,
                "PowerOff",
                "Power Off"
            )
        )
        self.display(image)

    def done(self):
        image = Image.new("RGB", (self.width, self.height))
        image.paste(
            self.baseImageCenterIcon(
                -1,
                [],
                "Done",
                "Done"
            )
        )
        self.display(image)

    def network(self,text="Automated Oven"):
        image = Image.new("RGB", (self.width, self.height))
        image.paste(
            self.baseImageCenterIcon(
                -1,
                [],
                "Wifi",
                text
            )
        )
        self.display(image)

    async def setBacklight(self, percent):
        self.backlight.duty_cycle = int(65535 * percent / 100)
        self.e.config.set('backlight',percent)
        return True

    async def getBacklight(self):
        return int((self.backlight.duty_cycle * 100) / 65535)
