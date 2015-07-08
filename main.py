#!/usr/bin/env python2
# -*- coding:utf8 -*-

import os
from NIU import Frame

if __name__ == "__main__":
    cwd = os.path.abspath(os.path.dirname(__file__))
    frame = Frame("Juniu Connect Manager", "1.2", cwd)
    frame.load_plugins()
    frame.loop()
