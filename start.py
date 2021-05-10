import pyautogui
import pydirectinput

from argparse import ArgumentParser
from os.path import join
from time import sleep

from config.config_manager import Config
from joystick_api.joystickapi import JoystickAPI


class Joy2Train:
    DEFAULT_CONFIG_FILE = join("config", "config.json")
    DEFAULT_NEUTRAL_VAL = 32767

    def __init__(self, conf_file=None, input_test=False):
        if cfg_file is None:
            self.config = Config(self.DEFAULT_CONFIG_FILE)
        else:
            self.config = Config(conf_file)

        self.api = JoystickAPI(joystick_oem_name=self.config.get_joystick_name())
        self.joystick = self.api.get_joystick()

        self.axis_state_collector = {}
        self.button_state_collector = {}

        self.test_mode = input_test

    @staticmethod
    def _determine_zone(axis_value, zone_mapping):
        for zone_name in zone_mapping:
            zone = zone_mapping[zone_name]

            if zone.min == 0:
                zone.min -= 1
            if zone.max == 65535:
                zone.max += 1

            if zone.min < axis_value < zone.max:
                return zone.id

    @staticmethod
    def press_key(key, wait=0.3):
        key_combo = key.split("-")

        for key in range(0, len(key_combo)):
            print("pressing {}".format(key_combo[key]))
            pydirectinput.keyDown(key_combo[key])

        sleep(wait)

        for key in reversed(range(0, len(key_combo))):
            print("releasing {}".format(key_combo[key]))
            pydirectinput.keyUp(key_combo[key])

    def _axis_zonal_to_keypress(self, previous_value, previous_zone, train_function_name, on_increase, on_decrease):
        axis_name = self.config.get_joy_axis_name_by_train_function_name(train_function_name)
        axis = self.joystick.get_axis(axis_name)
        zone_mapping = self.config.get_zone_mapping(train_function_name=train_function_name)
        if axis.changed:
            current_value = axis.value
            current_zone = self._determine_zone(current_value, zone_mapping)
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

    def _axis_endpoint_to_keypress(self, train_function_name, on_low, on_high, neutral_value=None):
        if neutral_value is None:
            neutral_value = self.DEFAULT_NEUTRAL_VAL
        axis_name = self.config.get_joy_axis_name_by_train_function_name(train_function_name)
        axis = self.joystick.get_axis(axis_name)

        if axis.changed:
            if train_function_name not in self.axis_state_collector.keys():
                self.axis_state_collector[train_function_name] = {"less_than_neutral": False,
                                                                  "more_than_neutral": False}

            if axis.value < neutral_value:
                if not self.axis_state_collector[train_function_name]["less_than_neutral"]:
                    self.axis_state_collector[train_function_name]["less_than_neutral"] = True
                    print("---{}---".format(axis_name))
                    self.press_key(on_low, wait=0.1)

            elif axis.value > neutral_value:
                if not self.axis_state_collector[train_function_name]["more_than_neutral"]:
                    self.axis_state_collector[train_function_name]["more_than_neutral"] = True
                    print("+++{}+++".format(axis_name))
                    self.press_key(on_high, wait=0.1)

            elif axis.value == neutral_value:
                del self.axis_state_collector[train_function_name]

    def _button_to_keypress(self, button_name, key_name):
        if button_name not in self.button_state_collector.keys():
            self.button_state_collector[button_name] = False

        button = self.joystick.get_button(button_name)

        if button.pressed:
            if not self.button_state_collector[button_name]:
                self.button_state_collector[button_name] = True
                print("+++{}+++".format(button_name))
                self.press_key(key_name)
        elif button_name in self.button_state_collector.keys():
            del self.button_state_collector[button_name]

    def _manage_zonal(self, train_function_name, train_function):
        if train_function_name not in self.axis_state_collector.keys():
            self.axis_state_collector[train_function_name] = {"zone": 0, "value": 0}

        zone = self.axis_state_collector[train_function_name]["zone"]
        value = self.axis_state_collector[train_function_name]["value"]

        value, zone = self._axis_zonal_to_keypress(previous_value=value,
                                                   previous_zone=zone,
                                                   train_function_name=train_function_name,
                                                   on_increase=train_function["on_increase"],
                                                   on_decrease=train_function["on_decrease"])

        self.axis_state_collector[train_function_name]["zone"] = zone
        self.axis_state_collector[train_function_name]["value"] = value

    def _manage_endpoint(self, train_function_name, train_function):
        try:
            neutral_value = train_function["neutral"]
        except KeyError:
            neutral_value = None
        self._axis_endpoint_to_keypress(train_function_name=train_function_name,
                                        on_low=train_function["on_low"],
                                        on_high=train_function["on_high"],
                                        neutral_value=neutral_value)

    @staticmethod
    def _show_joystick_values(joystick_values):
        axes = joystick_values["axes"]
        buttons = joystick_values["buttons"]
        pov = joystick_values["pov"]

        for axis in axes:
            if axis.changed:
                print("Axis {}: {}".format(axis.name, axis.value))

        for button in buttons:
            if button.pressed:
                print("Button {} is pressed.".format(button.name))

        for pov_dir in pov:
            if pov_dir.pressed:
                print("Pov direction: {}".format(pov_dir.name))

    def main(self):
        while True:
            joystick_values = self.api.poll_joystick(self.joystick)

            if self.test_mode:
                self._show_joystick_values(joystick_values)

            else:
                for train_function_name in self.config.get_mapped_functions():
                    train_function = self.config.get_train_function(train_function_name)

                    if train_function["type"] == "zonal" and self.config.zone_map_exists(train_function_name):
                        self._manage_zonal(train_function_name=train_function_name,
                                           train_function=train_function)

                    elif train_function["type"] == "endpoint":
                        self._manage_endpoint(train_function_name=train_function_name,
                                              train_function=train_function)

                    elif train_function["type"] == "button":
                        self._button_to_keypress(button_name=train_function["joy_button"],
                                                 key_name=train_function["kbd_button"])


if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument("--config", required=False, help="Config file path and name.")
    ap.add_argument("--input-test", required=False, action='store_true', help="Allows to check your joystick's values "
                                                                              "for configuration.")
    args = ap.parse_args()
    if args.config:
        cfg_file = args.config
    else:
        cfg_file = None
    J2T = Joy2Train(conf_file=cfg_file, input_test=args.input_test)
    print("Press Ctrl + c to quit.")
    J2T.main()
