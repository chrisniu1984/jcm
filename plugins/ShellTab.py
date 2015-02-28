# -*- coding:utf-8 -*-

import os
import os.path
import signal
import copy

from gi.repository import Gdk, Gtk, GObject, Vte
from gi.repository.GdkPixbuf import Pixbuf

from NIU import Frame, AbsTab, TabHead, Term

class ShellTab(AbsTab):
    @staticmethod
    def get_type():
        return "shell";

    def __init__(self, frame):
        self.frame = frame
        self.cfg = None

        # head
        self.head = TabHead(frame, img="shell.png")
        self.head.set_clone_clicked(self.__on_clone_clicked)
        self.head.set_close_clicked(self.__on_close_clicked)

        # body
        self.term = Term()
        self.term.SET_TITLE_CHANGED(self.__on_title_changed);
        self.term.connect("child-exited", self.__on_child_exited)
        self.term.show_all()

    def on_head(self):
        return self.head

    def on_body(self):
        return self.term

    def on_focus(self):
        self.term.grab_focus()

    def do_open(self, cfg):
        self.cfg = cfg
        cwd = None
        if cfg.has_key("cwd"):
            cwd = cfg["cwd"]

        cmd = ['/bin/bash']
        self.childpid = self.term.RUN(cmd, cwd)

    def do_close(self):
        if self.childpid > 0:
            os.kill(self.childpid, signal.SIGKILL)
            self.childpid = 0

        self.frame.del_tab(self)
        return True

    def __on_child_exited(self, widget, stat):
        self.childpid = 0
        self.do_close()

    def __on_clone_clicked(self, widget, data=None):
        # get my cwd
        pidpath = "/proc/%u/cwd" % (self.childpid)
        cwd = os.path.realpath(pidpath);

        cfg = copy.copy(self.cfg)
        cfg["cwd"] = cwd
        self.frame.run(cfg)

    def __on_close_clicked(self, widget, data=None):
        self.do_close()

    def __on_title_changed(self, title):
        self.head.set_title(title);
