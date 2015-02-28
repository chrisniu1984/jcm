# -*- coding:utf-8 -*-

import os
import os.path
import signal
import copy

from gi.repository import Gdk, Gtk, GObject, Vte
from gi.repository.GdkPixbuf import Pixbuf

from NIU import Frame, AbsTab, Term

IMG_TYPE="shell.png"
IMG_CLOSE="close.png"
IMG_CLONE="clone.png"

MENU_SIZE = 16

class ShellTab(AbsTab):
    @staticmethod
    def get_type():
        return "shell";

    def __init__(self, frame):
        self.frame = frame
        self.cfg = None

        # head
        self.hbox = Gtk.HBox(False, 0)
        self.img = self.frame.load_img(IMG_TYPE, MENU_SIZE);
        self.hbox.pack_start(self.img, False, False, 0)
        self.label = Gtk.Label("  SHELL  ")
        self.hbox.pack_start(self.label, False, False, 0)

        self.clone = Gtk.Button()
        self.clone.set_image(self.frame.load_img(IMG_CLONE, 16))
        self.clone.set_relief(Gtk.ReliefStyle.NONE)
        self.clone.connect("clicked", self.__on_clone_clicked)
        self.hbox.pack_start(self.clone, False, False, 0);

        self.button = Gtk.Button()
        self.button.set_image(self.frame.load_img(IMG_CLOSE, 16))
        self.button.set_relief(Gtk.ReliefStyle.NONE)
        self.button.connect("clicked", self.__on_close_clicked)
        self.hbox.pack_start(self.button, False, False, 0);

        self.hbox.show_all()

        # body
        self.term = Term()
        self.term.SET_TITLE_CHAGED(self.__on_title_changed);
        self.term.connect("child-exited", self.__on_child_exited)
        self.term.show_all()

    def head(self):
        return self.hbox

    def body(self):
        return self.term

    def focus(self):
        self.term.grab_focus()

    def open(self, cfg):
        self.cfg = cfg
        cwd = None
        if cfg.has_key("cwd"):
            cwd = cfg["cwd"]

        cmd = ['/bin/bash']
        self.childpid = self.term.RUN(cmd, cwd)

    def close(self):
        if self.childpid > 0:
            os.kill(self.childpid, signal.SIGKILL)
            self.childpid = 0

        self.frame.del_tab(self)
        return True

    def __on_child_exited(self, widget, stat):
        self.childpid = 0
        self.close()

    def __on_clone_clicked(self, widget, data=None):
        pidpath = "/proc/%u/cwd" % (self.childpid)
        cwd = os.path.realpath(pidpath);
        cfg = copy.copy(self.cfg)
        cfg["cwd"] = cwd
        self.frame.run(cfg)

    def __on_close_clicked(self, widget, data=None):
        self.close()

    def __on_title_changed(self, title):
        self.label.set_text(title);
