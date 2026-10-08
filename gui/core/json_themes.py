# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////

# IMPORT PACKAGES AND MODULES
# ///////////////////////////////////////////////////////////////
import json
import os
import sys

# IMPORT SETTINGS
# ///////////////////////////////////////////////////////////////
from gui.core.json_settings import Settings

# APP THEMES
# ///////////////////////////////////////////////////////////////
class Themes(object):
    # LOAD SETTINGS
    # ///////////////////////////////////////////////////////////////
    setup_settings = Settings()
    _settings = setup_settings.items

    @classmethod
    def resolve_theme_path(cls, theme_name):
        theme_file = f"{theme_name}.json"
        app_path = os.path.abspath(os.getcwd())
        module_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        candidates = []
        if getattr(sys, "frozen", False):
            candidates.append(os.path.normpath(os.path.join(os.path.dirname(sys.executable), "gui", "themes", theme_file)))
            candidates.append(os.path.normpath(os.path.join(os.path.dirname(sys.executable), "lib", "gui", "themes", theme_file)))

        candidates.extend(
            [
                os.path.normpath(os.path.join(app_path, "gui", "themes", theme_file)),
                os.path.normpath(os.path.join(module_root, "gui", "themes", theme_file)),
                os.path.normpath(os.path.join(module_root, "lib", "gui", "themes", theme_file)),
            ]
        )

        unique_candidates = []
        for candidate in candidates:
            if candidate not in unique_candidates:
                unique_candidates.append(candidate)

        for candidate in unique_candidates:
            if os.path.isfile(candidate):
                return candidate

        return unique_candidates[0]

    # INIT SETTINGS
    # ///////////////////////////////////////////////////////////////
    def __init__(self):
        super(Themes, self).__init__()

        # DICTIONARY WITH SETTINGS
        self.items = {}
        self.settings_path = self.resolve_theme_path(self._settings.get("theme_name", "default"))

        # DESERIALIZE
        self.deserialize()

    # SERIALIZE JSON
    # ///////////////////////////////////////////////////////////////
    def serialize(self):
        # WRITE JSON FILE
        with open(self.settings_path, "w", encoding='utf-8') as write:
            json.dump(self.items, write, indent=4)

    # DESERIALIZE JSON
    # ///////////////////////////////////////////////////////////////
    def deserialize(self):
        # READ JSON FILE
        with open(self.settings_path, "r", encoding='utf-8') as reader:
            settings = json.loads(reader.read())
            self.items = settings


