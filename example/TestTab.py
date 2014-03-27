# -*- coding:utf-8 -*-

import gtk
import vte

import Frame

class TestTab(Frame.AbsTab):
    @staticmethod
    def get_type():
        return "test";

    def __init__(self, frame):
        self.frame = frame
        # head
        self.hbox = gtk.HBox(False, 0)

        self.label = gtk.Label("test")
        self.hbox.pack_start(self.label)
        self.button = gtk.Button()
        self.button.set_image(gtk.image_new_from_file(self.frame.res_icon_close))
        self.button.set_relief(gtk.RELIEF_NONE)
        self.button.connect("clicked", self._on_close_clicked, None)

        self.hbox.pack_start(self.button, False, False, 0);
        self.hbox.show_all()
        self.vte = vte.Terminal()

    def head(self):
        return self.label

    def body(self):
        return self.vte

    def focus(self):
        pass

    def open(self, cfg):
        pass

    def close(self):
        return True
