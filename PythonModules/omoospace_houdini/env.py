import hou
import os
from pathlib import Path

from hutil.Qt.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QTextEdit,
)
from hutil.Qt import QtCore

from omoospace import (
    Omoospace, get_route_str,
    create_omoospace, format_name, reveal_in_explorer
)
from configparser import ConfigParser
config = ConfigParser()

BACKUP_NAMES = ["old", "Bak", "bak", ".bak", "Backup", "backup"]
HDA_PATHS = ["Contents/HDAs"]
HDA_EXTS = [".hda", ".otl"]


class OmoospaceConfig():
    def __init__(self):
        self.config_path = Path(Path.home(), ".omoospace_houdini.ini")

    def set_config(self, key: str, value):
        if not self.config_path.is_file():
            with self.config_path.open("w", encoding="utf-8") as f:
                pass

        config.read(self.config_path, encoding="utf-8")

        if 'Common' not in config:
            config['Common'] = {}

        config['Common'][key] = str(value)

        with self.config_path.open("w", encoding="utf-8") as f:
            config.write(f)

    def get_config(self, key: str):
        if not self.config_path.is_file():
            with self.config_path.open("w", encoding="utf-8") as f:
                pass

        config.read(self.config_path, encoding="utf-8")

        try:
            return config['Common'][key]
        except:
            return None

    @property
    def path_mode(self):
        return self.get_config("path_mode") or "unc"

    @path_mode.setter
    def path_mode(self, path_mode):
        self.set_config("path_mode", path_mode)

    def switch_path_mode(self, path_mode: str = None):
        if path_mode is None:
            path_mode = "unc" if self.path_mode == "mnt" else "mnt"

        set_env(path_mode)
        self.path_mode = path_mode
        print(f"Path mode was changed to {path_mode.upper()}")


def resolve_mapped(path):
    """on windows path resolve will return UNC path."""

    path = Path(path).resolve()
    mapped_paths = []
    for drive in 'ZYXWVUTSRQPONMLKJIHGFEDCBA':
        root = Path('{}:/'.format(drive))
        try:
            mapped_paths.append(root / path.relative_to(root.resolve()))
        except (ValueError, OSError):
            pass

    return min(mapped_paths, key=lambda x: len(str(x)), default=path)


def load_env(path_mode: str):
    try:
        file_path = Path(hou.hipFile.path()).resolve()
        omoos_path = Omoospace(file_path).root_path

        if path_mode == "mnt":
            omoos_path = resolve_mapped(omoos_path)

        omoos_path_str = omoos_path.as_posix()
        route_str = get_route_str(file_path)
    except:
        omoos_path_str = get_voidspace().root_path.as_posix()
        route_str = "Void_Untitled"

    backup_dir_str = Path(omoos_path_str, "StagedData/Backup").as_posix()

    return omoos_path_str, route_str, backup_dir_str


def get_voidspace():
    try:
        voidspace = Omoospace(Path(Path.home(), "Void"))
    except:
        voidspace = create_omoospace(
            name="Void",
            root_dir=Path.home(),
            description="Default omoospace inited by houdini as default project.",
            reveal_in_explorer=False
        )
    return voidspace


def set_env(path_mode):
    omoos_path_str, route_str, backup_dir_str = load_env(path_mode)
    if hou.getenv('JOB') != omoos_path_str:
        hou.hscript(f"setenv JOB = {omoos_path_str}")
        print(f"$JOB was changed to: {omoos_path_str}")

    if hou.getenv('ROUTE') != route_str:
        # hou.putenv not save to file. so use hscript "setenv"
        hou.hscript(f"setenv ROUTE = {route_str}")
        print(f"$ROUTE was changed to: {route_str}")

    hou.putenv("HOUDINI_BACKUP_DIR", backup_dir_str)
    return omoos_path_str, route_str, backup_dir_str


def import_hda(project_path):
    if project_path:
        for hda_path in HDA_PATHS:
            for root, dirs, files in os.walk(Path(project_path, hda_path)):
                dirs[:] = [d for d in dirs if d not in BACKUP_NAMES]
                for file in files:
                    hda = Path(root, file)
                    if hda.suffix in HDA_EXTS:
                        hou.hda.installFile(hda.as_posix())


def on_hip_open():
    if hou.getenv('ROUTE') is None:
        omoos_path_str, route_str, backup_dir_str = load_env(
            OmoospaceConfig().path_mode
        )
        
        hou.putenv("JOB", omoos_path_str)
        hou.putenv("ROUTE", route_str)
        hou.putenv("HOUDINI_BACKUP_DIR", backup_dir_str)
    else:
        omoos_path_str = hou.getenv('JOB')
        route_str = hou.getenv('ROUTE')

    print(f"Current omoospace path $JOB: {omoos_path_str}")
    print(f"Current subspace route $ROUTE: {route_str}")

    # set lop render gallery source
    hou.parm("/stage/rendergallerysource").set(
        "$JOB/StagedData/Galleries/`$ROUTE`/Rendergallery.db")

    # import HDA from omoospace
    import_hda(omoos_path_str)


def on_hip_save():
    omoos_path_str, route_str, backup_dir_str = set_env(
        OmoospaceConfig().path_mode)

    import_hda(omoos_path_str)



