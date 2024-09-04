import time
from PCA9685 import PCA9685

class RobotArm:
    CH_CLAW = 0
    CH_WRIST = 1
    CH_JOINT1 = 2
    CH_JOINT2 = 3
    CH_JOINT3 = 4
    CH_JOINT4 = 5
    def __init__(self, debug=False):
        self.pwm = PCA9685(0x40, debug=debug)
        self.pwm.setPWMFreq(50)
        self.pwm.setServoPulse(self.CH_CLAW, 500)
        time.sleep(0.02)
        self.pwm.setServoPulse(self.CH_WRIST, 500)
        time.sleep(0.02)
        self.pwm.setServoPulse(self.CH_JOINT1, 700)
        time.sleep(0.02)
    
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
    
    def greet(self):
        self.turn(self.CH_CLAW, 500, 1500, 5)
        self.turn(self.CH_CLAW, 1500, 500, 5) 
        self.turn(self.CH_CLAW, 500, 1500, 5)
        self.turn(self.CH_CLAW, 1500, 500, 5) 
    
    def smile(self):
        # self.turn(self.CH_WRIST, 500, 2500, 5)
        self.turn(self.CH_WRIST, 500, 2000, 5)
        self.turn(self.CH_WRIST, 2000, 500, 5)
    
    def pat(self):
        self.turn(self.CH_JOINT1, 700, 1000)
        self.turn(self.CH_JOINT1, 1000, 700)
        self.turn(self.CH_JOINT1, 700, 1000)
        self.turn(self.CH_JOINT1, 1000, 700)

if __name__ == "__main__":
    robot_arm = RobotArm()
    robot_arm.test()
