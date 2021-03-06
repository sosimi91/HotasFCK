from collections import OrderedDict
from json import loads
from os.path import isfile
from pyautogui import isValidKey


class Zone:
    def __init__(self, name, zone_id, min_value, max_value, wait=None):
        self.name = name
        self.id = zone_id
        self.min = min_value
        self.max = max_value
        if wait:
            self.wait = wait
        else:
            self.wait = 0.3


class Config:
    def __init__(self, config_file):
        if isfile(config_file):
            self.config_file = config_file
        else:
            raise AttributeError("Invalid config file path.")

        self.mapping_types_template = {
            "zonal": ["axis", "on_increase", "on_decrease"],
            "endpoint": ["axis", "on_low", "on_high"],
            "button": ["joy_button", "kbd_button"]
        }
        self.config_lvl0_fields = ["joystick", "selected_train", "trains"]
        self.config_mapping_fields = ["accelerator", "direction", "pause"]

        self.validate_buttons_on_pyautogui = ["on_increase", "on_decrease", "on_low", "on_high", "kbd_button"]

        self.parsed = self._load_cfg()

    def _validate_cfg(self, data):
        for field in self.config_lvl0_fields:
            if field not in data.keys():
                raise ValueError("\'{}\' field is missing from the config.".format(field))

        if data["selected_train"] not in data["trains"].keys():
            raise ValueError("The selected train ({}) is not in the defined trains.".format(data["selected_train"]))

        if "mapping" not in data["joystick"].keys():
            raise ValueError("Mapping is missing from the joystick's config.")

        mapping_data = data["joystick"]["mapping"]

        for field in self.config_mapping_fields:
            if field not in mapping_data.keys():
                raise ValueError("\'{}\' field is missing from the config's joystick mapping.".format(field))

        for train_function in mapping_data:
            if "type" not in mapping_data[train_function].keys():
                raise ValueError("Missing train function mapping type at {}.".format(train_function))
            train_function_type = mapping_data[train_function]["type"]
            if train_function_type not in self.mapping_types_template.keys():
                raise ValueError("Invalid train function mapping type at {}.".format(train_function))

            train_function_data = mapping_data[train_function]
            for required_key in self.mapping_types_template[train_function_type]:
                if required_key not in train_function_data.keys():
                    raise ValueError("Missing property in {}.".format(train_function))

                if required_key in self.validate_buttons_on_pyautogui:
                    kbd_key = train_function_data[required_key]

                    if "-" in kbd_key:
                        check_keys = kbd_key.split("-")
                    else:
                        check_keys = [kbd_key]

                    for key in check_keys:
                        if not isValidKey(key):
                            raise ValueError("This key is not accepted by the framework: {}.".format(kbd_key))

    def _load_cfg(self):
        with open(self.config_file, "r") as cfg:
            data = cfg.read()
        cfg_json = loads(data)
        self._validate_cfg(cfg_json)
        return cfg_json

    def get_joy_axis_name_by_train_function_name(self, train_function_name):
        return self.parsed["joystick"]["mapping"][train_function_name]["axis"]

    def get_mapped_functions(self):
        return sorted(self.parsed["joystick"]["mapping"].keys())

    def get_joystick_name(self):
        return self.parsed["joystick"]["name"]

    def get_train_function(self, train_function_name):
        return self.parsed["joystick"]["mapping"][train_function_name]

    def get_zone_mapping(self, train_function_name):
        zones_data = OrderedDict()
        selected_train = self.parsed["selected_train"]
        zones = self.parsed["trains"][selected_train]["zones"][train_function_name]
        global_wait = None
        for zone_name in sorted(zones):
            if zone_name == "default_wait":
                global_wait = zones[zone_name]
            else:
                _zone = zones[zone_name]
                try:
                    wait = _zone["wait"]
                except KeyError:
                    wait = global_wait if global_wait else None
                zones_data[zone_name] = Zone(name=_zone["name"],
                                             zone_id=_zone["id"],
                                             min_value=_zone["min"],
                                             max_value=_zone["max"],
                                             wait=wait)

        return zones_data

    def zone_map_exists(self, train_function_name):
        selected_train = self.parsed["selected_train"]
        return train_function_name in self.parsed["trains"][selected_train]["zones"]
