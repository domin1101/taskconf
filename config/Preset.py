import datetime
import logging
import uuid

from TaskConf.config.ConfigurationBlock import ConfigurationBlock, NotFoundError
import collections
import copy

class Preset:

    def __init__(self, data=None, base_preset=None, file=None):
        """Creates a new preset.

        Args:
            data(dict): The raw json data of the preset.
            base_preset(Preset): The base preset object for this preset.
            file(str): The filename which contained the preset.
        """
        self.prefix = ""
        self.base_preset = base_preset
        self.file = file
        self.try_number = 0
        self._printed_settings = set()
        self.logger = None

        if data is not None:
            self.set_data(data)
        else:
            self.data = {}
            self.name = ""
            self.uuid = ""
            self.creation_time = 0
            self.config = None
            self.abstract = False

    def set_data(self, new_data):
        if "uuid" not in new_data:
            new_data["uuid"] = str(uuid.uuid4())
        if "creation_time" not in new_data:
            new_data["creation_time"] = datetime.datetime.now().timestamp()

        if self.base_preset is not None:
            new_data['config'] = self.base_preset.diff_config(new_data['config'])

        self.data = new_data
        self.config = ConfigurationBlock(new_data["config"])
        self.name = new_data["name"] if "name" in new_data else self._generate_name()
        self.uuid = new_data["uuid"]
        self.creation_time = datetime.datetime.fromtimestamp(new_data["creation_time"])
        self.abstract = "abstract" in new_data and bool(new_data["abstract"])

    def _generate_name(self):
        name = ""
        if self.base_preset is not None and self.base_preset.base_preset is not None:
            name += self.base_preset.name + ": "
        flattened_data = self.config.flatten()
        for key in flattened_data:
            name += key + ": " + str(flattened_data[key]) + " - "

        if name.endswith(" - "):
            name = name[:-3]
        elif name is "":
            name = "empty"

        self.data["name"] = name
        return name

    def _get_value(self, name, value_type):
        """Returns the configuration with the given name and the given type.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.

        Args:
            name(str): The name of the configuration.
            value_type(str): The desired type of the configuration value.

        Returns:
            object: The value of the configuration in the requested type.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into the requested type.
        """
        try:
            value = getattr(self.config, 'get_' + value_type)(name)
        except NotFoundError:
            if self.base_preset is None:
                raise
            else:
                value = self.base_preset._get_value(name, value_type)

        return value

    def _get_value_with_fallback(self, name, fallback, value_type):
        """Returns the configuration with the given name or the fallback name and the given type.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.
            value_type(str): The desired type of the configuration value.

        Returns:
            object: The value of the configuration in the requested type.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into the requested type.
        """
        name = self.prefix + name

        try:
            value = self._get_value(name, value_type)
        except NotFoundError:
            if fallback is not None:
                value = self._get_value(self.prefix + fallback, value_type)
            else:
                raise

        if name not in self._printed_settings and self.logger is not None:
            self.logger.log("Using " + name + " = " + str(value))
            self._printed_settings.add(name)

        return value

    def get_int(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as an integer.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            int: The integer value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into an integer.
        """
        return self._get_value_with_fallback(name, fallback, 'int')

    def get_string(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as a string.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            str: The string value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into a string.
        """
        return self._get_value_with_fallback(name, fallback, 'string')

    def get_float(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as a float.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            float: The float value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into a float.
        """
        return self._get_value_with_fallback(name, fallback, 'float')

    def get_bool(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as a bool.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            bool: The bool value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into a bool.
        """
        return self._get_value_with_fallback(name, fallback, 'bool')

    def get_list(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as a list.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            list: The list value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into a list.
        """
        return self._get_value_with_fallback(name, fallback, 'list')

    def get_with_prefix(self, prefix):
        """Clones this preset and adds an additional prefix.

        Args:
            prefix(str): The additional prefix.

        Returns:
            Preset: The new preset with the requested prefix.
        """
        preset = self.clone()
        preset.prefix = self.prefix + prefix + "/"
        return preset

    def clone(self):
        preset = Preset(base_preset=self.base_preset)
        preset.name = self.name
        preset.config = self.config
        preset.data = self.data
        preset.prefix = self.prefix
        preset.file = self.file
        preset.try_number = self.try_number
        preset.uuid = self.uuid
        preset.creation_time = self.creation_time
        return preset

    def get_experiment_name(self):
        """Returns the name of the described experiment.

        Returns:
            str: The experiment name.
        """
        return self.name + " (try " + str(self.try_number) + ")"

    def set_logger(self, new_logger):
        """Cleans the list of all already printed settings.

        After calling this, the configuration log will start from scratch again.

        Args:
            new_logger: A new logger which should be used for future logging.
        """
        self._printed_settings.clear()
        self.logger = new_logger

    def compose_config(self):
        config = copy.deepcopy(self.data['config'])
        if self.base_preset is not None:
            config = self._deep_update(self.base_preset.compose_config(), config)
        return config

    def _deep_update(self, d, u):
        for k, v in u.items():
            if isinstance(v, collections.Mapping):
                d[k] = self._deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def diff_config(self, config):
        new_flattened_data = ConfigurationBlock(config).flatten()
        old_flattened_data = self.config.flatten()
        for key in new_flattened_data:
            if key in old_flattened_data and old_flattened_data[key] == new_flattened_data[key]:
                keys = key.split('/')

                config_block = config
                for single_key in keys[:-1]:
                    config_block = config_block[single_key]
                del config_block[keys[-1]]

                keys.pop()
                while len(keys) > 0:
                    config_block = config
                    for single_key in keys[:-1]:
                        config_block = config_block[single_key]
                    if len(config_block[keys[-1]]) == 0:
                        del config_block[keys[-1]]
                        keys.pop()
                    else:
                        break

        return config
