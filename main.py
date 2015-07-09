#!/usr/bin/env python2
# -*- coding:utf8 -*-

import os
from NIU import Frame

def get_ver(cwd):
    verfile = cwd + "/version"
    if os.path.exists(verfile) == False:
        return ""

    f = open(verfile)
    ver = f.read()
    f.close()
    return ver.strip()

if __name__ == "__main__":
    cwd = os.path.abspath(os.path.dirname(__file__))
    ver = get_ver(cwd)

    frame = Frame("Juniu Connect Manager", ver, cwd)
    frame.load_plugins()
    frame.loop()
