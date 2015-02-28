#!/usr/bin/env python2
# -*- coding:utf8 -*-

import os
from NIU import Frame

if __name__ == "__main__":
    #禁用 menu proxy for ubuntu
    os.environ["UBUNTU_MENUPROXY"] = "0"

    cwd = os.path.abspath(os.path.dirname(__file__))
    frame = Frame("Juniu Connect Manager", "1.1.1", cwd)
    frame.load_plugins()
    frame.show()
