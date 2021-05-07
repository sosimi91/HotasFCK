import pyautogui
from joystick_api.joystickapi import JoystickAPI
from time import sleep


class Joy2Train:
    def __init__(self):
        self.api = JoystickAPI()
        self.joystick = self.api.get_joystick()

    @staticmethod
    def zone(axis_value):
        if axis_value < 5000:
            return -6
        elif 5000 < axis_value < 10000:
            return -5
        elif 10000 < axis_value < 15000:
            return -4
        elif 15000 < axis_value < 20000:
            return -3
        elif 20000 < axis_value < 25000:
            return -2
        elif 25000 < axis_value < 32767:
            return -1
        elif axis_value == 32767:
            return 0
        elif 32767 < axis_value < 40000:
            return 1
        elif 40000 < axis_value < 45000:
            return 2
        elif 45000 < axis_value < 50000:
            return 3
        elif 50000 < axis_value < 55000:
            return 4
        elif 55000 < axis_value < 60000:
            return 5
        elif 60000 < axis_value:
            return 6

    def press_key(self, key):
        pyautogui.keyDown(key)
        sleep(0.3)
        pyautogui.keyUp(key)

    def main(self):
        prev_throttle_value = 0
        prev_throttle_zone = 0
        while True:
            joystick_data = self.api.poll_joystick(self.joystick)
            axes = joystick_data["axes"]
            buttons = joystick_data["buttons"]
            pov = joystick_data["pov"]

            throttle = self.joystick.get_axis("JOY_Z")
            if throttle.changed:
                current_value = throttle.value
                current_zone = self.zone(current_value)
                if (prev_throttle_value < current_value) and (prev_throttle_zone < current_zone):
                    print("---")
                    self.press_key("d")
                elif (prev_throttle_value > current_value) and (prev_throttle_zone > current_zone):
                    print("+++")
                    self.press_key("a")

                prev_throttle_value = current_value
                prev_throttle_zone = current_zone


if __name__ == "__main__":
    J2T = Joy2Train()
    J2T.main()
