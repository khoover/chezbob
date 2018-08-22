
import configparser

import os.path

SECRET_FILENAME = ".chezbob_secrets.ini"
HOME_DIR = os.path.expanduser("~")

SECRET_PATH = os.environ.get("CHEZBOB_SECRETS_PATH",
                             os.path.join(HOME_DIR, SECRET_FILENAME))

_config = None


def _get_parser():
    global _config
    if not _config:
        _config = configparser.ConfigParser()
        _config.read(SECRET_PATH)
    return _config


def get_secret(name):
    section, name = name.split(".", maxsplit=1)
    _config = _get_parser()
    return _config.get(section, name)

