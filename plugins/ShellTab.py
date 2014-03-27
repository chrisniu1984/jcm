# -*- coding:utf-8 -*-

import os
import signal

import gtk
import vte

import Frame

class ShellTab(Frame.AbsTab):
    @staticmethod
    def get_type():
        return "shell";

    def __init__(self, frame):
        self.frame = frame

        # head
        self.hbox = gtk.HBox(False, 0)
        self.label = gtk.Label("Local Shell")
        self.hbox.pack_start(self.label)
        self.button = gtk.Button()
        self.button.set_image(gtk.image_new_from_file(self.frame.res_icon_close))
        self.button.set_relief(gtk.RELIEF_NONE)
        self.button.connect("clicked", self._on_close_clicked)

        self.hbox.pack_start(self.button, False, False, 0);
        self.hbox.show_all()

        # body
        self.vte = vte.Terminal()
        self.vte.set_font_from_string("WenQuanYi Micro Hei Mono 11");
        self.vte.set_scrollback_lines(1024);
        self.vte.set_scroll_on_keystroke(1);
        self.vte.connect("button-press-event", self._on_vte_button_press);
        self.vte.show_all()

    def head(self):
        return self.hbox

    def body(self):
        return self.vte

    def focus(self):
        self.vte.grab_focus()

    def open(self, cfg):
        cmd = ['/bin/bash']
        self.childpid = self.vte.fork_command(cmd[0], cmd, os.getcwd())
        if self.childpid > 0:
            self.vte.connect('child-exited', self._on_child_exited)

    def close(self):
        if self.childpid > 0:
            os.kill(self.childpid, signal.SIGKILL)
            self.childpid = 0

        self.frame.del_tab(self)
        return True

    def _on_child_exited(self, widget):
        self.childpid = 0
        self.close()

    def _on_close_clicked(self, widget, data=None):
        self.close()

    def _on_vte_button_press(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            if self.vte.get_has_selection():
                self.vte.copy_clipboard()
                self.vte.select_none()
            else:
                self.vte.paste_clipboard()
