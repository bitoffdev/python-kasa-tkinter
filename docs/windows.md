# Windows

## Build

First, install chocolatey.

In powershell, run `choco install python --version 3.7.2`. **The version of python is important**. This project requires Python 3.6+ for typing and asyncio. Furthermore, pyinstaller only supports up to Python 3.7 as of January, 2021.

### Install poetry

In powershell, run `C:\Python37\python.exe -m pip install --user poetry`.

### Install Python packages

In powershell, run `C:\Python37\python.exe -m poetry install`.

### Build a single executable with PyInstaller

In powershell, run `C:\Python37\python.exe -m poetry run pyinstaller kasatk.spec`.

In powershell, your freshly built executable with `.\dist\kasatk.exe`.

## Troubleshooting

- PyInstaller hangs on "Building PKG (CArchive) kasatk.pkg"
  - This should only take ~5 seconds. It it seems to hang, try
    deleting the `build` and `dist` directories.

