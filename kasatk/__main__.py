# We cannot use relative imports in the __main__.py file with PyInstaller. If
# we do, we will get an error.
#
# https://github.com/pyinstaller/pyinstaller/issues/2560#issuecomment-377917879
#
from kasatk.gui import main


main()
