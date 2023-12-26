import hou
import os
from pathlib import Path
from omoospace import Omoospace, get_route_str, create_omoospace

BACKUP_NAMES = ["old", "Bak", "bak", ".bak", "Backup", "backup"]
HDA_PATHS = ["Contents/HDAs"]
HDA_EXTS = [".hda", ".otl"]


def set_env():
    try:
        file_path = Path(hou.hipFile.path()).resolve()
        omoos_path = Omoospace(file_path).root_path.as_posix()

        route_str = get_route_str(file_path)

        print(f"Current omoospace path $JOB: {omoos_path}")
        print(f"Current subspace route $ROUTE: {route_str}")

    except:
        try:
            default_omoos = Omoospace(Path(Path.home(), "Void"))
        except:
            default_omoos = create_omoospace(
                name="Void",
                root_dir=Path.home(),
                description="Default omoospace inited by houdini as default project.",
                reveal_in_explorer=False
            )
        omoos_path = default_omoos.root_path.as_posix()

        route_str = "Untitled"

        print("No omoospace detected, so...")
        print(f"set default omoospace path $JOB: {omoos_path}")
        print(f"set default subspace route $ROUTE: {route_str}")

    # hou.putenv not save to file. so use hscript "setenv"
    hou.hscript(f"setenv JOB = {omoos_path}")
    hou.hscript(f"setenv ROUTE = {route_str}")

    backup_dir = Path(omoos_path, "StagedData/Backup").as_posix()
    hou.putenv("HOUDINI_BACKUP_DIR", backup_dir)


def import_hda():
    project_path = hou.getenv("JOB")
    if project_path:
        for hda_path in HDA_PATHS:
            for root, dirs, files in os.walk(Path(project_path, hda_path)):
                dirs[:] = [d for d in dirs if d not in BACKUP_NAMES]
                for file in files:
                    hda = Path(root, file)
                    if hda.suffix in HDA_EXTS:
                        hou.hda.installFile(hda.as_posix())

def init_hip():
    set_env()
    import_hda()