import time
import gex

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
        self.colors = [0x000000 for _ in range(0, LIGHT_CNT)]

        client = gex.Client(gex.TrxRawUSB())
        self.btn = gex.DIn(client, 'btn')
        self.neo = gex.Neopixel(client, 'neo')
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
            self.colors = [0x009900 for _ in range(0, LIGHT_CNT)]
            self.break_s = BK_TIME * 60

        elif phase == PH_BREAK_OVER:
            self.colors = [0x662200 for _ in range(0, LIGHT_CNT)]

        elif phase == PH_WORK:
            self.colors = [0x990000 for _ in range(0, LIGHT_CNT)]
            self.work_s = WK_TIME * 60

        elif phase == PH_WORK_OVER:
            self.colors = [0x113300 for _ in range(0, LIGHT_CNT)]

        self.phase = phase

    def extinguish(self, dark, total):
        per_light = total / LIGHT_CNT
        lights = int((dark + per_light / 2) / per_light)
        for n in range(0, LIGHT_CNT - lights):
            self.colors[n] = 0x000000

    def tick(self):
        if self.phase == PH_BREAK:
            self.break_s -= 1
            print("Break remain: %d s" % self.break_s)
            self.extinguish(self.break_s, BK_TIME * 60)

            if self.break_s == 0:
                self.switch(PH_BREAK_OVER)

        elif self.phase == PH_WORK:
            self.work_s -= 1
            print("Work remain: %d s" % self.work_s)
            self.extinguish(self.work_s, WK_TIME * 60)

            if self.work_s == 0:
                self.switch(PH_WORK_OVER)

        self.display()

    def run(self):
        while True:
            time.sleep(1)
            self.tick()


a = Pymodoro()
a.run()
