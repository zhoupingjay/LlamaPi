import time
from PCA9685 import PCA9685

class RobotArm:
    CH_CLAW = 0         # 500 (open) - 1500 (close)
    CH_WRIST = 1        # 500 (horizontal) - 1500 (vertical) - 2000 - 2500 (~horizontal)
    CH_JOINT1 = 2       # 280 (lowest) - 1400 (parallel with J2, highest) - 2400
    CH_JOINT2 = 3       # 280 (lowest) - 1800 (parallel with J3, highest) - 2000
    CH_JOINT3 = 4       # 280 - 400 (higest, vertical) - 1400 (horizontal)
    CH_BASE = 5         # 280 -> counterclockwise -> 2400
    def __init__(self, debug=False):
        self.pwm = PCA9685(0x40, debug=debug)
        self.pwm.setPWMFreq(50)
        self.reset()

    def reset(self):
        self.pwm.setServoPulse(self.CH_BASE, 280)
        time.sleep(0.1)

        self.pwm.setServoPulse(self.CH_JOINT3, 1000)
        time.sleep(0.1)

        self.pwm.setServoPulse(self.CH_JOINT2, 1200)
        time.sleep(0.1)

        self.pwm.setServoPulse(self.CH_JOINT1, 700)
        time.sleep(0.1)

        self.pwm.setServoPulse(self.CH_WRIST, 500)
        time.sleep(0.1)

        self.pwm.setServoPulse(self.CH_CLAW, 500)
        time.sleep(0.1)
    
    def turn(self, ch, start=500, end=2500, speed=1):
        step = 10 if start < end else -10
        step = step * speed
        for i in range(start, end, step):
            self.pwm.setServoPulse(ch, i)
            time.sleep(0.02)
    
    def test(self):
        self.greet()
        time.sleep(1)
        self.smile()
        time.sleep(1)
        self.pat()
        time.sleep(1)
        self.retrieve()
    
    def greet(self):
        self.reset()
        time.sleep(0.02)
        self.turn(self.CH_CLAW, 500, 1500, 4)
        time.sleep(0.02)
        self.turn(self.CH_CLAW, 1500, 500, 4)
        time.sleep(0.02) 
        self.turn(self.CH_CLAW, 500, 1500, 4)
        time.sleep(0.02)
        self.turn(self.CH_CLAW, 1500, 500, 4)
        time.sleep(0.02)
        self.reset()
    
    def smile(self):
        self.reset()
        # self.turn(self.CH_WRIST, 500, 2500, 5)
        self.turn(self.CH_WRIST, 500, 2000, 4)
        time.sleep(0.02)
        self.turn(self.CH_WRIST, 2000, 500, 4)
        time.sleep(0.02)
        self.reset()
    
    def pat(self):
        self.reset()
        self.turn(self.CH_JOINT1, 700, 1000)
        time.sleep(0.02)
        self.turn(self.CH_JOINT1, 1000, 700)
        time.sleep(0.02)
        self.turn(self.CH_JOINT1, 700, 1000)
        time.sleep(0.02)
        self.turn(self.CH_JOINT1, 1000, 700)
        time.sleep(0.02)
        self.reset()
    
    def retrieve(self):
        self.reset()
        self.turn(self.CH_JOINT2, 1200, 300)
        time.sleep(0.02)
        # JOINT1 is already in place after reset
        self.turn(self.CH_CLAW, 500, 1400)
        time.sleep(0.02)
        self.turn(self.CH_JOINT2, 300, 1200)
        time.sleep(0.02)
        self.turn(self.CH_BASE, 280, 1000)
        time.sleep(0.5)
        self.turn(self.CH_CLAW, 1400, 500)
        time.sleep(0.5)
        self.turn(self.CH_BASE, 1000, 280)
        time.sleep(0.02)
        self.reset()

if __name__ == "__main__":
    robot_arm = RobotArm()
    robot_arm.test()
