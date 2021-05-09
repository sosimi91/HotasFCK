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

    def _axis_zonal_to_keypress(self, previous_value, previous_zone, axis_name, on_increase, on_decrease):
        axis = self.joystick.get_axis(axis_name)
        if axis.changed:
            current_value = axis.value
            current_zone = self.zone(current_value)
            if (previous_value < current_value) and (previous_zone < current_zone):
                print("---{}---".format(axis_name))
                for press in range(0, (current_zone - previous_zone)):
                    self.press_key(on_decrease)
            elif (previous_value > current_value) and (previous_zone > current_zone):
                print("+++{}+++".format(axis_name))
                for press in range(0, (previous_zone - current_zone)):
                    self.press_key(on_increase)

            previous_value = current_value
            previous_zone = current_zone
        return previous_value, previous_zone

    def _axis_endpoint_to_keypress(self, axis_name, on_low, on_high, neutral_value=32767):
        axis = self.joystick.get_axis(axis_name)
        if axis.changed:
            if axis.value < neutral_value:
                print("---{}---".format(axis_name))
                self.press_key(on_low)
            elif axis.value > neutral_value:
                print("+++{}+++".format(axis_name))
                self.press_key(on_high)

    def main(self):
        prev_throttle_value = 0
        prev_throttle_zone = 0

        prev_break_value = 0
        prev_break_zone = 0
        while True:
            joystick_data = self.api.poll_joystick(self.joystick)
            axes = joystick_data["axes"]
            buttons = joystick_data["buttons"]
            pov = joystick_data["pov"]

            prev_throttle_value, prev_throttle_zone = self._axis_zonal_to_keypress(prev_throttle_value,
                                                                                   prev_throttle_zone,
                                                                                   "JOY_Z", "a", "d")

            prev_break_value, prev_break_zone = self._axis_zonal_to_keypress(prev_break_value,
                                                                             prev_break_zone,
                                                                             "JOY_Y", ";", "'")

            self._axis_endpoint_to_keypress("JOY_U", "y", "u")


if __name__ == "__main__":
    J2T = Joy2Train()
    J2T.main()
