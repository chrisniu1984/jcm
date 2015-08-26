# -*- coding:utf-8 -*-

import os
import os.path
import signal
import copy

from gi.repository import Gdk, Gtk, GObject, Vte
from gi.repository.GdkPixbuf import Pixbuf

from NIU import Frame, AbsTab, TabHead, Term, Expect, Misc

ICON_FMAN="fman.png"

class shell(AbsTab):
    def __init__(self, frame):
        self.frame = frame
        self.cfg = None

        # head
        self.head = TabHead(frame, img="shell.png")
        self.head.set_close_clicked(self.__on_close_clicked)

        # body
        self.term = Term()
        self.term.SET_TITLE_CHANGED(self.__on_title_changed);
        self.term.connect("child-exited", self.__on_child_exited)
        self.term.show_all()

    def HEAD(self):
        return self.head

    def BODY(self):
        return self.term

    def HBAR(self):
        if not hasattr(self, "hbar"):
            item = Gtk.Button()
            item.set_relief(Gtk.ReliefStyle.NONE)
            item.set_image(self.frame.load_icon(ICON_FMAN))
            item.connect("clicked", self.__on_fman_clicked)
            self.hbar = item

        return self.hbar

    def on_focus(self):
        self.term.grab_focus()

    def __cfg_cwd(self):
        if not self.cfg.has_key("cwd"):
            return None

        cwd = self.cfg["cwd"]
        if cwd.startswith("~"):
            home = os.environ["HOME"]
            cwd = home + cwd[1:] 
        return cwd

    def on_open(self, cfg):
        self.cfg = cfg
        cwd = self.__cfg_cwd()
        cmd = ['/bin/bash']
        self.childpid = self.term.RUN(cmd, cwd)

    def on_close(self):
        if self.childpid > 0:
            os.kill(self.childpid, signal.SIGKILL)
            self.childpid = 0

        self.frame.del_tab(self)
        return True

    def __on_child_exited(self, widget, stat):
        self.childpid = 0
        self.on_close()

    def __on_close_clicked(self, widget, data=None):
        self.on_close()

    def __on_title_changed(self, title):
        self.head.set_title(title);

        idx = title.find(":")
        if idx != -1:
            cwd = title[idx+1:].strip()
        else:
            cwd = "~"

        if cwd.startswith("~"):
            cwd = os.environ["HOME"] + cwd[1:] 

        self.cwd = cwd

    def __on_fman_clicked(self, widget):
        Misc.execute("xdg-open file://" + self.cwd + "/", cwd=self.cwd)

