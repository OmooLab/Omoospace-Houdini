# Omoospace for Houdini

This is the houdini editon of omoospace.

## Getting Started

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

### Add it to houdini

Create a env file in packages `houdiniX.Y/packages/env.json`

```json
{
  "package_path": [
    "Path/to/Omoospace-Houdini/Packages"
    ]
}
```
