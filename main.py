#!/usr/bin/env python2
# -*- coding:utf8 -*-

import os
import sys
import gtk

from Frame import Frame, AbsTab

if __name__ == "__main__":
    frame = Frame("Juniu Connect Manager", "1.0.0")
    frame.load_plugins()
    frame.show()

    gtk.main()
