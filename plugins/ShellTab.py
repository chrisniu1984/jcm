# -*- coding:utf-8 -*-

import os
import signal

from gi.repository import Gdk, Gtk, GObject, Vte
from gi.repository.GdkPixbuf import Pixbuf

import Frame

IMG_CLOSE="close.svg"

def vte_terminal_RUN(term, cmd):
    if hasattr(term, "spawn_sync"):
        return term.spawn_sync(Vte.PtyFlags.DEFAULT, os.getcwd(),
                            cmd, None, GObject.SPAWN_SEARCH_PATH, None, None)[1]
    elif hasattr(term, "fork_command_full"):
        return term.fork_command_full(Vte.PtyFlags.DEFAULT, os.getcwd(),
                            cmd, None, GObject.SPAWN_SEARCH_PATH, None, None)[1]

def vte_terminal_CONNECT_CHILD_EXITED(term, _on_child_exited_old, _on_child_exited):
    if hasattr(term, "spawn_sync"):
        term.connect('child-exited', _on_child_exited)
    elif hasattr(term, "fork_command_full"):
        term.connect('child-exited', _on_child_exited_old)
    
class ShellTab(Frame.AbsTab):
    @staticmethod
    def get_type():
        return "shell";

    def __init__(self, frame):
        self.frame = frame

        # head
        self.hbox = Gtk.HBox(False, 0)
        self.label = Gtk.Label("SHELL")
        self.hbox.pack_start(self.label, False, False, 0)
        self.button = Gtk.Button()
        self.button.set_image(self.frame.load_img(IMG_CLOSE, 16))
        self.button.set_relief(Gtk.ReliefStyle.NONE)
        self.button.connect("clicked", self._on_close_clicked)

        self.hbox.pack_start(self.button, False, False, 0);
        self.hbox.show_all()

        # body
        self.term = Vte.Terminal()
        #self.term.set_font_from_string("WenQuanYi Micro Hei Mono 11");
        self.term.set_scrollback_lines(1024);
        self.term.set_scroll_on_keystroke(1);
        self.term.connect("button-press-event", self._on_term_button_press);
        self.term.show_all()

    def head(self):
        return self.hbox

    def body(self):
        return self.term

    def focus(self):
        self.term.grab_focus()

    def open(self, cfg):
        cmd = ['/bin/bash']
        self.childpid = vte_terminal_RUN(self.term, cmd)

        if self.childpid > 0:
            vte_terminal_CONNECT_CHILD_EXITED(self.term,
                self._on_child_exited_old, self._on_child_exited)

    def close(self):
        if self.childpid > 0:
            os.kill(self.childpid, signal.SIGKILL)
            self.childpid = 0

        self.frame.del_tab(self)
        return True

    def _on_child_exited(self, widget, x):
        self.childpid = 0
        self.close()

    def _on_child_exited_old(self, widget):
        self.childpid = 0
        self.close()

    def _on_close_clicked(self, widget, data=None):
        self.close()

    def _on_term_button_press(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            if self.term.get_has_selection():
                self.term.copy_clipboard()
                self.term.select_none()
            else:
                self.term.paste_clipboard()
