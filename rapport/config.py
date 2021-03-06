# Copyright 2013 Sascha Peilicke
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import os
import shutil
try:
    import ConfigParser as configparser  # Py2
except ImportError:
    import configparser

import rapport.config


def _get_config_dirs():
    """Return a list of directories where config files may be located.

    The following directories are returned::

      ~/.rapport/
      /etc/rapport/
    """
    config_dirs = [
        os.path.expanduser(os.path.join("~", ".rapport")),
        os.path.join("/", "etc", "rapport"),
        os.path.abspath(os.path.join("rapport", "config"))
    ]
    return config_dirs


def find_config_files():
    """Return a list of default configuration files.
    """

    config_files = []

    for config_dir in _get_config_dirs():
        path = os.path.join(config_dir, "rapport.conf")
        if os.path.exists(path):
            config_files.append(path)

    return list(filter(bool, config_files))


def init_user():
    """Create and populate the ~/.rapport directory tree if it's not existing.

    Doesn't interfere with already existing directories or configuration files.
    """
    user_conf_dir = os.path.expanduser(os.path.join("~", ".rapport"))
    user_conf_file = os.path.join(user_conf_dir, "rapport.conf")

    if not os.path.exists(user_conf_dir):
        if rapport.config.get_int("rapport", "verbosity") >= 1:
            print("Create user directory {0}".format(user_conf_dir))
        os.makedirs(user_conf_dir)
    for subdir in ["plugins", "reports", "templates/plugin", "templates/email", "templates/web"]:
        user_conf_subdir = os.path.join(user_conf_dir, subdir)
        if not os.path.exists(user_conf_subdir):
            if rapport.config.get_int("rapport", "verbosity") >= 1:
                print("Create user directory {0}".format(user_conf_subdir))
            os.makedirs(user_conf_subdir)
        if subdir == "reports" and not (os.stat(user_conf_subdir).st_mode & 0o777) == 0o700:
            if rapport.config.get_int("rapport", "verbosity") >= 1:
                print("Set secure directory permissions for {0}".format(user_conf_subdir))
            os.chmod(user_conf_subdir, 0o700)
    if not os.path.exists(user_conf_file):
        if rapport.config.get_int("rapport", "verbosity") >= 1:
            print("Create user configuration {0}".format(user_conf_file))
        default_config = os.path.abspath(os.path.join(os.path.splitext(__file__)[0], "rapport.conf"))
        shutil.copyfile(default_config, user_conf_file)

    if not (os.stat(user_conf_file).st_mode & 0o777) == 0o600:
        if rapport.config.get_int("rapport", "verbosity") >= 1:
            print("Set secure file permissions for {0}".format(user_conf_file))
        os.chmod(user_conf_file, 0o600)


CONF = None


def load():
    global CONF
    config = configparser.SafeConfigParser()

    if not find_config_files():
        init_user()
    config.read(find_config_files()[0])
    CONF = config
    return CONF


def get(section, option, default=None):
    if CONF.has_option(section, option):
        return CONF.get(section, option)
    else:
        return default


def get_int(section, option, default=-1):
    return int(get(section, option, default))


def set(section, option, value):
    CONF.set(section, option, str(value))


def plugins():
    for section in CONF.sections():
        if section.startswith("plugin:"):
            name, alias = section.split(":")[1:]
            plugin = {"name": name, "alias": alias}
            for option in CONF.options(section):
                plugin[option] = CONF.get(section, option)
            yield plugin
