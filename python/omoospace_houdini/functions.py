import json
import os
from pathlib import Path
from .utils import copy_to_dir
import hou

from omoospace import (
    Omoospace,
    create_omoospace,
    format_name
)

from hutil.Qt.QtWidgets import (
    QDialog,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
)

import hutil.Qt.QtCore as QtCore

NODE_CONFIG_PATH = Path(__file__).parent.parent.parent / "nodes.json"

with NODE_CONFIG_PATH.open('r') as f:
    data = json.load(f)
    EXPORT_PARMS = data['export_parms']
    IMPORT_PARMS = data['import_parms']
    COPY_PARENT_MARKERS = data['copy_parent_markers']


def organize_export_paths(nodes):
    for node in nodes:
        node_type = node.type().name()
        node_name = node.name()
        present = EXPORT_PARMS.get(node_type)
        if present:
            for parm_name in present.keys():
                parm_value = present[parm_name]
                node.parm(parm_name).set(parm_value)
                print(f"Set {node_name}.{parm_name} to {parm_value}")


class OrganizeExportPaths(QDialog):
    # self.ui only Main Window
    def __init__(self, import_path_dict, omoospace):
        super(OrganizeExportPaths, self).__init__()

        self.omoospace = omoospace
        self.import_path_dict = import_path_dict

        # Create a QListWidget
        list_widget = QListWidget()

        # init import_path_dict copy_parent switch
        for node_parm in self.import_path_dict.keys():
            import_path_raw: str = self.import_path_dict[node_parm]['import_path_raw']

            copy_parent = False
            for mark in COPY_PARENT_MARKERS:
                if mark in import_path_raw:
                    copy_parent = True
                    break

            self.import_path_dict[node_parm]['copy_parent'] = copy_parent
            changed_path_raw = self.get_changed_path_raw(
                node_parm, copy_parent)

            item = QListWidgetItem(
                f"{node_parm}: {import_path_raw} => {changed_path_raw}")
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable |
                          QtCore.Qt.ItemIsEnabled)

            if copy_parent:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)

            item.setData(QtCore.Qt.UserRole, node_parm)
            list_widget.addItem(item)

        list_widget.itemChanged.connect(self.handle_item_checked)

        button = QPushButton("Confrim")
        button.clicked.connect(self.copy)

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel(
            "Copy it's parent directroy or not?"))
        main_layout.addWidget(list_widget)
        main_layout.addWidget(button)
        self.setLayout(main_layout)

        self.setWindowTitle("Organize Export Paths")
        self.setMinimumWidth(1000)

    def handle_item_checked(self, item):
        node_parm = item.data(QtCore.Qt.UserRole)
        if item.checkState() == QtCore.Qt.Checked:
            self.import_path_dict[node_parm]['copy_parent'] = True
        else:
            self.import_path_dict[node_parm]['copy_parent'] = False

        item.setText(self.get_change_str(node_parm))

    def get_change_str(self, node_parm):
        import_path_raw: str = self.import_path_dict[node_parm]['import_path_raw']
        changed_path_raw: str = self.get_changed_path_raw(node_parm)

        return f"{node_parm}: {import_path_raw} => {changed_path_raw}"

    def get_changed_path_raw(self, node_parm, copy_parent=None):
        copy_parent = copy_parent or self.import_path_dict[node_parm]['copy_parent']
        import_path_raw: str = self.import_path_dict[node_parm]['import_path_raw']
        import_path_eval: str = self.import_path_dict[node_parm]['import_path_eval']

        parent_str: str = Path(import_path_eval).parent.name
        end_str: str = Path(import_path_raw).name

        if self.is_out_of_omoospace(node_parm):
            return f"$JOB/ExternalData/Collected/{parent_str}/{end_str}" \
                if copy_parent else f"$JOB/ExternalData/Collected/{end_str}"
        else:
            import_path_raw_str = Path(import_path_raw).resolve().as_posix()
            return f"$JOB{import_path_raw_str.removeprefix(self.omoospace.root_path.as_posix())}"

    def is_out_of_omoospace(self, node_parm):
        import_path_eval: str = self.import_path_dict[node_parm]['import_path_eval']
        return self.omoospace.root_path not in Path(import_path_eval).resolve().parents

    def copy(self):
        changed_node_parms = []
        import_path_dict = self.import_path_dict
        omoospace = self.omoospace

        # copy files and directroies
        with hou.InterruptableOperation(
            "Copy to ExternalData",
            open_interrupt_dialog=True
        ) as operation:
            for index, node_parm in enumerate(import_path_dict.keys()):
                node = import_path_dict[node_parm]['node']
                parm = import_path_dict[node_parm]['parm']
                import_path_eval: str = self.import_path_dict[node_parm]['import_path_eval']

                copy_parent: bool = import_path_dict[node_parm]['copy_parent']
                changed_path_raw: str = self.get_changed_path_raw(node_parm)

                if self.is_out_of_omoospace(node_parm):
                    source = Path(import_path_eval)
                    try:
                        copy_to_dir(
                            source.parent if copy_parent else source,
                            omoospace.externaldata_path / 'Collected',
                            exist_ok=True
                        )
                    except:
                        continue

                node.parm(parm).set(changed_path_raw)
                changed_node_parms.append(node_parm)

                percent = float(index) / float(len(import_path_dict.keys()))
                operation.updateProgress(percent)

        # print report
        report_message = ""
        for node_parm in import_path_dict.keys():
            if node_parm in changed_node_parms:
                report_message += f"[√] {self.get_change_str(node_parm)}\n"
            else:
                report_message += f"[×] {self.get_change_str(node_parm)}\n"

        report = hou.ui.displayMessage(
            report_message,
            title="Report"
        )

        print(report_message)
        os.startfile(omoospace.externaldata_path / 'Collected')
        self.close()


def organize_import_paths(nodes):
    import_path_dict = {}
    omoospace = Omoospace(hou.getenv('JOB'))

    def add_to_dict(node, parm):
        import_path_eval = node.evalParm(parm)
        import_path_raw = node.parm(parm).rawValue()

        if import_path_raw and ("$JOB" not in import_path_raw):
            import_path_dict[f"{node_name}.{parm}"] = {
                "node": node,
                "parm": parm,
                "import_path_raw": import_path_raw,
                "import_path_eval": import_path_eval
            }

    for node in nodes:
        node_name = node.name()
        node_type = node.type().name()
        parms: list[str] = IMPORT_PARMS.get(node_type) or []
        for parm in parms:
            if parm.endswith("*"):
                index = 1
                while True:
                    parm_name = parm.removesuffix("*") + str(index)
                    try:
                        add_to_dict(node, parm_name)
                    except:
                        break
                    index += 1

            else:
                add_to_dict(node, parm)

    if len(import_path_dict.keys()) > 0:
        dialog = OrganizeExportPaths(import_path_dict, omoospace)
        dialog.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
        dialog.show()
    else:
        print("No parms need to change.")


class SaveToNewOmoospace(QDialog):
    # self.ui only Main Window
    def __init__(self):
        super(SaveToNewOmoospace, self).__init__()

        self.omoospace_home_input = hou.qt.InputField(
            data_type=hou.qt.InputField.StringType,
            num_components=1,
            label="Home Directory"
        )
        default_directory = Path.home().as_posix()
        self.omoospace_home_input.setValue(default_directory)
        self.omoospace_home_input.valueChanged.connect(self.on_path_changed)

        omoospace_home_btn = hou.qt.FileChooserButton()
        omoospace_home_btn.setFileChooserTitle("Where to store new omoospace?")
        omoospace_home_btn.setFileChooserFilter(hou.fileType.Directory)
        omoospace_home_btn.setFileChooserDefaultValue(default_directory)
        omoospace_home_btn.setFileChooserMode(hou.fileChooserMode.Read)
        omoospace_home_btn.fileSelected.connect(self.on_file_selected)

        omoospace_home_layout = QHBoxLayout()
        omoospace_home_layout.setContentsMargins(0, 0, 0, 0)
        omoospace_home_layout.addWidget(self.omoospace_home_input)
        omoospace_home_layout.addWidget(omoospace_home_btn)
        omoospace_home = QWidget()
        omoospace_home.setLayout(omoospace_home_layout)

        self.omoospace_name_input = hou.qt.InputField(
            data_type=hou.qt.InputField.StringType,
            num_components=1,
            label="Omoospace Name"
        )
        self.omoospace_name_input.valueChanged.connect(self.on_path_changed)

        self.subspace_name_input = hou.qt.InputField(
            data_type=hou.qt.InputField.StringType,
            num_components=1,
            label="Subspace Name"
        )
        self.subspace_name_input.valueChanged.connect(self.on_path_changed)

        self.hip_path_input = QLineEdit()
        self.hip_path_input.setEnabled(False)

        hip_path_layout = QHBoxLayout()
        hip_path_layout.setContentsMargins(0, 0, 0, 0)
        hip_path_layout.addWidget(hou.qt.FieldLabel("File Path"))
        hip_path_layout.addWidget(self.hip_path_input)
        hip_path = QWidget()
        hip_path.setLayout(hip_path_layout)

        self.save_to_btn = QPushButton('Save To')
        self.save_to_btn.clicked.connect(self.on_save_to)

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(omoospace_home)
        main_layout.addWidget(self.omoospace_name_input)
        main_layout.addWidget(self.subspace_name_input)
        main_layout.addWidget(hip_path)
        main_layout.addWidget(self.save_to_btn)
        self.setLayout(main_layout)

        self.setWindowTitle("Save to New Omoospace")
        self.setMinimumWidth(600)

    @property
    def omoospace_home(self) -> str:
        return self.omoospace_home_input.value()

    @property
    def omoospace_name(self) -> str:
        return self.omoospace_name_input.value()

    @property
    def subspace_name(self) -> str:
        return self.subspace_name_input.value() or self.omoospace_name_input.value()

    @property
    def hip_path(self) -> str:
        if self.omoospace_name == "" or self.omoospace_home == "":
            return ""

        path = Path(
            self.omoospace_home,
            format_name(self.omoospace_name), 'SourceFiles',
            f'{format_name(self.subspace_name)}.hip'
        )
        return path.as_posix()

    def on_file_selected(self, file_path):
        self.omoospace_home_input.setValue(file_path)

    def on_path_changed(self):
        self.hip_path_input.setText(self.hip_path)

    def on_save_to(self):
        if self.omoospace_home == "":
            hou.ui.displayMessage(
                "Home Directory is required.",
                severity=hou.severityType.Warning
            )
            return

        if self.omoospace_name == "":
            hou.ui.displayMessage(
                "Omoospace Name is required.",
                severity=hou.severityType.Warning
            )
            return

        omoospace = create_omoospace(
            name=self.omoospace_name,
            root_dir=self.omoospace_home,
            reveal_in_explorer=False
        )
        hou.hipFile.save(self.hip_path)
        os.startfile(omoospace.sourcefiles_path)
        self.close()


def save_to_new_omoospace():
    dialog = SaveToNewOmoospace()
    dialog.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
    dialog.show()
