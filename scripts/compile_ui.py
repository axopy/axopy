"""
Compiles PyQt UI templates and places the corresponding modules in the source
`templates` directory. Run from the project root directory.
"""

import os
from PyQt5 import uic


SRC = 'templates'
DEST = os.path.join('axopy', 'templates')


if __name__ == '__main__':
    uic.compileUiDir(SRC, map=lambda src, name: (DEST, name))
