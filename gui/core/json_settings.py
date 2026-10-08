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


DEFAULT_SETTINGS = {
    "app_name": "PyUtility v2",
    "version": "v2.1.0",
    "copyright": "Projeto PAP 2026",
    "year": 2026,
    "theme_name": "default",
    "custom_title_bar": True,
    "startup_size": [1400, 720],
    "minimum_size": [960, 540],
    "lef_menu_size": {"minimum": 50, "maximum": 240},
    "left_menu_content_margins": 3,
    "left_column_size": {"minimum": 0, "maximum": 240},
    "right_column_size": {"minimum": 0, "maximum": 240},
    "time_animation": 500,
    "font": {
        "family": "Segoe UI",
        "title_size": 10,
        "text_size": 9,
    },
}


# APP SETTINGS
# ///////////////////////////////////////////////////////////////
class Settings(object):
    json_file = "settings.json"

    @classmethod
    def resolve_settings_path(cls):
        app_path = os.path.abspath(os.getcwd())
        module_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        candidates = []
        if getattr(sys, "frozen", False):
            candidates.append(os.path.normpath(os.path.join(os.path.dirname(sys.executable), cls.json_file)))

        candidates.extend(
            [
                os.path.normpath(os.path.join(app_path, cls.json_file)),
                os.path.normpath(os.path.join(module_root, cls.json_file)),
                os.path.normpath(os.path.join(module_root, "lib", cls.json_file)),
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
        super(Settings, self).__init__()

        # DICTIONARY WITH SETTINGS
        # Just to have objects references
        self.items = {}
        self.settings_path = self.resolve_settings_path()

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
        if not os.path.isfile(self.settings_path):
            print(f"WARNING: \"{self.json_file}\" not found! check in the folder {self.settings_path}")
            self.items = dict(DEFAULT_SETTINGS)
            try:
                with open(self.settings_path, "w", encoding='utf-8') as write:
                    json.dump(self.items, write, indent=4)
            except Exception:
                pass
            return

        # READ JSON FILE
        with open(self.settings_path, "r", encoding='utf-8') as reader:
            settings = json.loads(reader.read())
            self.items = settings


