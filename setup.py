from cx_Freeze import setup, Executable

build_exe_options = {
    "include_files": [
        ("settings.json", "settings.json"),
        ("gui/images", "lib/gui/images"),
        ("gui/themes", "lib/gui/themes"),
    ]
}

setup(
    name="PyUtility",
    version="2.1.0",
    description="PyUtility",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py")],
)