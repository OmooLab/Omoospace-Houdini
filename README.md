# Omoospace for Houdini

This is the houdini add-on of omoospace.

[中文文档](https://uj6xfhbzp0.feishu.cn/wiki/IFcwwNWfci6TpwkW6mUcvcJmnVf?from=from_copylink)

## Getting Started

### Installation

Download the latest release version of Omoospace-Houdini (choose your houdini python version).
[https://github.com/OmooLab/Omoospace-Houdini/releases](https://github.com/OmooLab/Omoospace-Houdini/releases)

Unzip all files to any directory.  
e.g. `path/to/Omoospace-Houdini`

Reference it's package path to houdini package json file `houdiniX.Y/packages/env.json`.

```json
// env.json
{
  ...
  "package_path": [
    ...
    "path/to/Omoospace-Houdini/Packages"
    ]
  ...
}
```

### Usage

## For Contributors

### Dependencies

- Python >= 3.9
- Houdini >= 19.5

Pull this repository.

```bash
$ git clone https://github.com/OmooLab/Omoospace-Houdini.git
$ cd Omoospace-Houdini
```

Create python virtualenv for Houdini 19.5.

```bash
$ pyenv global 3.9.10 # <- python verison of houdini 19.5
$ python -m venv PythonLib3.9
$ source PythonLib3.9/Scripts/activate
```

if you are using Houdini 20

```bash
$ pyenv global 3.10.10 # <- python verison of houdini 20
$ python -m venv PythonLib3.10
$ source PythonLib3.10/Scripts/activate
```

Install dependencies.

```bash
$ pip install -r requirements.txt
```
