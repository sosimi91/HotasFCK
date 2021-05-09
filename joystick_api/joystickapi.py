import ctypes
import winreg

from joystick_api.joy_caps import JOYCAPS
from joystick_api.joy_flags import *
from joystick_api.joy_info_ex import JOYINFOEX

from time import sleep


class Button:
    def __init__(self, name, mask_index):
        self.name = name
        self.mask_index = mask_index
        self.pressed = False

    def __repr__(self):
        return "{}{}".format(self.name, " - pressed" if self.pressed else "")


class Axis:
    def __init__(self, name):
        self.name = name
        self.value = 0
        self.changed = False

    def __repr__(self):
        return "{} - {}".format(self.name, str(self.value))


class PovDir:
    def __init__(self, name, mask_value):
        self.name = name
        self.mask_value = mask_value
        self.pressed = False

    def __repr__(self):
        return "{}{}".format(self.name, " - pressed" if self.pressed else "")


class Joystick:
    NO_BUTTON_STR = "Button {} not found."

    def __init__(self, axes=None, buttons=12, pov=True):
        if axes is None:
            axes = ["R", "U", "X", "Y", "Z"]
        self.driver_name = None
        self.oem_name = None
        self.number = None

        self.capabilities = JOYCAPS()

        self.info = JOYINFOEX()
        self.info.dwSize = ctypes.sizeof(JOYINFOEX)
        self.info.dwFlags = JOY_RETURNALL

        self.axes = [Axis(name="JOY_{}".format(axis))
                     for axis in axes]

        if pov:
            self.pov_dirs = [PovDir(pov, 4500 * p_index) for p_index, pov in enumerate(["N", "NE", "E", "SE",
                                                                                        "S", "SW", "W", "NW"])]
        else:
            self.pov_dirs = None

        self.buttons = [Button(name="BTN_{0:02}".format(btn + 1),
                               mask_index=buttons - btn - 1)
                        for btn in range(0, buttons)]

    def _get_item(self, what, where):
        for _item in where:
            if _item.name == what:
                return _item
        raise AttributeError(self.NO_BUTTON_STR.format(what))

    def get_button(self, name):
        return self._get_item(name, self.buttons)

    def get_axis(self, name):
        return self._get_item(name, self.axes)

    def get_pov(self, name):
        return self._get_item(name, self.pov_dirs)

    def get_pressed_buttons(self):
        pressed = []
        button_mask = "{0:0" + str(len(self.buttons)) + "b}"
        buttons_info = button_mask.format(self.info.dwButtons)
        for btn_index, button in enumerate(self.buttons):
            button.pressed = bool(int(buttons_info[button.mask_index]))
            if button.pressed:
                pressed.append(button)

        return pressed

    def get_axes(self, changed_only=False):
        for axis in self.axes:
            if axis.name == "JOY_R":
                axis.changed = axis.value != self.info.dwRpos
                axis.value = self.info.dwRpos

            elif axis.name == "JOY_U":
                axis.changed = axis.value != self.info.dwUpos
                axis.value = self.info.dwUpos

            elif axis.name == "JOY_V":
                axis.changed = axis.value != self.info.dwVpos
                axis.value = self.info.dwVpos

            elif axis.name == "JOY_X":
                axis.changed = axis.value != self.info.dwXpos
                axis.value = self.info.dwXpos

            elif axis.name == "JOY_Y":
                axis.changed = axis.value != self.info.dwYpos
                axis.value = self.info.dwYpos

            elif axis.name == "JOY_Z":
                axis.changed = axis.value != self.info.dwZpos
                axis.value = self.info.dwZpos

        if changed_only:
            return [axis for axis in self.axes if axis.changed]
        else:
            return self.axes

    def get_pov(self):
        if self.pov_dirs is not None:
            value = self.info.dwPOV

            for p_dir in self.pov_dirs:
                p_dir.pressed = value == p_dir.mask_value

            return self.pov_dirs
        else:
            return None


class JoystickAPI:
    JOY_NAME = "T.Flight Hotas X"
    SUB_PREFIX = "System\\CurrentControlSet\\Control\\"
    HWID_SUB_KEY_STR = SUB_PREFIX + "MediaResources\\Joystick\\{}\\CurrentJoystickSettings"
    OEM_NAME_SUB_KEY_STR = SUB_PREFIX + "MediaProperties\\PrivateProperties\\Joystick\\OEM\\{}"
    MISSING_REG_KEY_ERROR_STR = "Missing registry key."
    MISSING_JS_NUM_ERORR_STR = "Missing joystick number."
    OEM_NAME_STR = "OEMName"
    JS_OEM_NAME_STR = "Joystick{}"+OEM_NAME_STR
    NA_STR = "N/A"
    DRIVER_AND_OEM_NAME_STR = "Driver name: {}; OEM name: {}"
    JS_NOT_FOUND_ERROR_STR = "{} joystick not found"
    JS_DATA_STR = "Axes: {}; Buttons: {}; POV: {}"

    def __init__(self, joystick_oem_name=None):
        if joystick_oem_name is None:
            self.oem_name_of_searched_joy = self.JOY_NAME
        else:
            self.oem_name_of_searched_joy = joystick_oem_name
        self.dll = ctypes.windll.winmm
        self.joystick = Joystick()

    def _get_number_of_devices(self):
        try:
            number_of_joysticks = self.dll.joyGetNumDevs()
        except:
            number_of_joysticks = 0
        return number_of_joysticks

    def _get_oem_name(self, registry_key=None, joystick_number=None):
        if registry_key is None:
            if len(self.joystick.capabilities.szRegKey) > 0:
                registry_key = self.joystick.capabilities.szRegKey
            else:
                raise AttributeError(self.MISSING_REG_KEY_ERROR_STR)

        if joystick_number is None:
            if self.joystick.number:
                joystick_number = self.joystick.number
            else:
                raise AttributeError(self.MISSING_JS_NUM_ERORR_STR)

        sub_key = self.HWID_SUB_KEY_STR.format(registry_key)

        try:
            hwid_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key)
            hardware_id, _ = winreg.QueryValueEx(hwid_key, self.JS_OEM_NAME_STR.format(joystick_number + 1))
            sub_key_2 = self.OEM_NAME_SUB_KEY_STR.format(hardware_id)
            oname_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key_2)
            oem_name, _ = winreg.QueryValueEx(oname_key, self.OEM_NAME_STR)
            hwid_key.Close()
            oname_key.Close()
        except WindowsError:
            oem_name = self.NA_STR

        return oem_name

    def get_joystick(self, verbose=False):
        for joy_num in range(0, self._get_number_of_devices()):
            return_code = self.dll.joyGetDevCapsW(joy_num,
                                                  ctypes.pointer(self.joystick.capabilities),
                                                  ctypes.sizeof(self.joystick.capabilities))
            if return_code == 0:
                self.joystick.number = joy_num
                self.joystick.driver_name = self.joystick.capabilities.szPname

                self.joystick.oem_name = self._get_oem_name()

                if verbose:
                    print(self.DRIVER_AND_OEM_NAME_STR.format(self.joystick.driver_name,
                                                              self.joystick.oem_name))

                if self.joystick.oem_name == self.oem_name_of_searched_joy:
                    return self.joystick

        raise IOError(self.JS_NOT_FOUND_ERROR_STR.format(self.oem_name_of_searched_joy))

    def poll_joystick(self, joystick, verbose=False):
        joystick_connected = self.dll.joyGetPosEx(joystick.number, ctypes.pointer(joystick.info)) == 0
        if joystick_connected:
            axes = joystick.get_axes()
            buttons = joystick.get_pressed_buttons()
            pov = joystick.get_pov()

            if verbose:
                print(self.JS_DATA_STR.format(axes, buttons, pov))

            sleep(0.001)

            return {
                "axes": axes,
                "buttons": buttons,
                "pov": pov
            }

        else:
            raise IOError(self.JS_NOT_FOUND_ERROR_STR.format(joystick.oem_name))
