# Windows

## Build

First, install chocolatey.

In powershell, run `choco install python --version 3.7.2`. **The version of python is important**. This project requires Python 3.6+ for typing and asyncio. Furthermore, pyinstaller only supports up to Python 3.7 as of January, 2021.

### Install virtualenv and create a new environment

In powershell, run `C:\Python37\python.exe -m pip install --user virtualenv`.

In powershell, run `C:\Python37\python.exe -m virtualenv env`.

Note: From here onward, we will use the virtualenv's python with `.\env\Scripts\python.exe`.

### Install Python packages

In powershell, run `.\env\Scripts\python.exe -m pip install -r requirements.txt`.

### Build a single executable with PyInstaller

In powershell, run `.\env\Scripts\python.exe -m pip install pyinstaller`.

In powershell, run `.\env\Scripts\pyinstaller.exe .\kasatk.spec`.

In powershell, your freshly built executable with `.\dist\kasatk.spec`.