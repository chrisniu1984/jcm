#!/usr/bin/env python2
# -*- coding:utf8 -*-

import os
import sys

from gi.repository import Gtk

from Frame import Frame, AbsTab

#禁用 menu proxy for ubuntu
os.environ["UBUNTU_MENUPROXY"] = "0"

if __name__ == "__main__":
    frame = Frame("Juniu Connect Manager", "1.1.0")
    frame.load_plugins()
    frame.show()
