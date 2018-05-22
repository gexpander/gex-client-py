import time
import gex

# GEX pomodoro timer

# button btn
# neopixel neo

# this is an example of using GEX as a user interface.
# for practical use it would be better to make this into a standalone device with a custom firmware.

WK_TIME = 25
BK_TIME = 5
LIGHT_CNT = 30

PH_BREAK = 'Break'
PH_BREAK_OVER = 'BreakOver'
PH_WORK = 'Work'
PH_WORK_OVER = 'WorkOver'

class Pymodoro:
    def __init__(self):
        self.phase = PH_BREAK_OVER
        self.work_s = 0
        self.break_s = 0
        self.color = 0x000000
        self.colors = [0x000000 for _ in range(0, LIGHT_CNT)]

        self.client = gex.Client(gex.TrxRawUSB())
        self.btn = gex.DIn(self.client, 'btn')
        self.neo = gex.Neopixel(self.client, 'neo')
        self.btn.on_trigger([0], self.on_btn)

        self.switch(PH_BREAK_OVER)
        self.display()

    def display(self):
        self.neo.load(self.colors)

    def on_btn(self, snapshot, timestamp):
        if self.phase == PH_BREAK_OVER:
            self.switch(PH_WORK)
            
        elif self.phase == PH_WORK:
            self.switch(PH_WORK) # restart

        elif self.phase == PH_WORK_OVER:
            self.switch(PH_BREAK)

    def switch(self, phase):
        print("Switch to %s" % phase)

        if phase == PH_BREAK:
            self.color = 0x009900
            self.break_s = BK_TIME * 60

        elif phase == PH_BREAK_OVER:
            self.color = 0x662200

        elif phase == PH_WORK:
            self.color = 0x990000
            self.work_s = WK_TIME * 60

        elif phase == PH_WORK_OVER:
            self.color = 0x113300

        self.colors = [self.color for _ in range(0, LIGHT_CNT)]
        self.phase = phase

    def show_progress(self, dark, total):
        per_light = total / LIGHT_CNT
        lights = dark / per_light

        lights /= 2

        remainder = float(lights - int(lights))
        if remainder == 0:
            remainder = 1

        # print("lights %f, remainder %f" % (lights, remainder))
        for i in range(0, int(LIGHT_CNT/2)):
            if i < int((LIGHT_CNT/2)-lights):
                c = 0x000000
            elif i == int((LIGHT_CNT/2)-lights):
                r = (self.color&0xFF0000)>>16
                g = (self.color&0xFF00)>>8
                b = self.color&0xFF
                c = (int(r*remainder))<<16 | (int(g*remainder))<<8 | (int(b*remainder))
            else:
                c = self.color

            self.colors[i] = c
            self.colors[LIGHT_CNT - 1 - i] = c

    def tick(self, elapsed):
        if self.phase == PH_BREAK:
            self.break_s -= elapsed
            # print("Break remain: %d s" % self.break_s)
            self.show_progress(self.break_s, BK_TIME * 60)

            if self.break_s <= 0:
                self.switch(PH_BREAK_OVER)

        elif self.phase == PH_WORK:
            self.work_s -= elapsed
            # print("Work remain: %d s" % self.work_s)
            self.show_progress(self.work_s, WK_TIME * 60)

            if self.work_s <= 0:
                self.switch(PH_WORK_OVER)

        self.display()

    def run(self):
        step=0.5
        try:
            while True:
                time.sleep(step)
                self.tick(step)
        except KeyboardInterrupt:
            self.client.close()
            print() # this puts the ^C on its own line


a = Pymodoro()
a.run()
