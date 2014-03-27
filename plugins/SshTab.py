# -*- coding:utf-8 -*-

import os
import signal

import gtk
import vte

import Frame

class SshTab(Frame.AbsTab):
    @staticmethod
    def get_type():
        return "ssh";

    def __init__(self, frame):
        self.frame = frame

        # head
        self.hbox = gtk.HBox(False, 0)

        self.label = gtk.Label("")
        self.hbox.pack_start(self.label)
        self.button = gtk.Button()
        self.button.set_image(gtk.image_new_from_file(self.frame.res_icon_close))
        self.button.set_relief(gtk.RELIEF_NONE)
        self.button.connect("clicked", self._on_close_clicked, None)

        self.hbox.pack_start(self.button, False, False, 0);
        self.hbox.show_all()

        # body
        self.vbox = gtk.VBox(False, 0)

        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_BOTH);
        self.vbox.pack_start(self.toolbar, False, False, 0)
        self.vbox.show_all()

        self.vte = vte.Terminal()
        self.vte.set_font_from_string("WenQuanYi Micro Hei Mono 11");
        self.vte.set_scrollback_lines(1024);
        self.vte.set_scroll_on_keystroke(1);
        self.vte.connect("button-press-event", self._on_vte_button_press);
        self.vbox.pack_start(self.vte, True, True, 0)
        self.vbox.show_all()

    def head(self):
        return self.hbox

    def body(self):
        return self.vbox

    def focus(self):
        self.vte.grab_focus()

    def _extra_process(self, extra):
        for btn in extra:
            item = gtk.ToolButton(None, btn[0])
            self.toolbar.insert(item, -1);

            menu = gtk.Menu();
            item.connect("clicked", self._on_btn_clicked, menu);

            i = 0
            for cmd in btn[1:]:
                if cmd.has_key("title"):
                    mitem = gtk.MenuItem(cmd["title"]);
                else:
                    mitem = gtk.MenuItem(cmd["name"]);
                mitem.connect("activate", self._on_cmd_clicked, cmd);
                menu.attach(mitem, 0, 1, i, i+1);
                i = i + 1
            menu.show_all()

            # |
            item = gtk.SeparatorToolItem()
            self.toolbar.insert(item, -1)

        self.toolbar.show_all()

    def open(self, cfg):
        self.cfg = cfg
        self._extra_process(cfg["extra"])
        self.vte.feed("connecting ... " + cfg["host"] + ":" + cfg["port"] + "\r\n")
        self.vte.feed("\r\n")

        self.label.set_text(cfg["name"])
        cmd = ['/usr/bin/ssh', cfg["user"] + "@" + cfg["host"], "-p", cfg["port"]]
        self.childpid = self.vte.fork_command(cmd[0], cmd, os.getcwd())

        self.expect_key = "password:"
        self.expect_val = cfg["pass"] + "\n"
        if self.childpid > 0:
            self.vte.connect('child-exited', self._on_child_exited)
            self.vte.connect('contents-changed', self._on_contents_changed)

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

    def capture_text(self, terminal,text2,text3,text4):
        return True

    def _on_contents_changed(self, widget, data=None):
        text = self.vte.get_text(self.capture_text).strip()

        # expect
        if len(self.expect_key) > 0 and text.endswith(self.expect_key):
            self.vte.feed_child(self.expect_val+"\n")
            self.expect_key = ""
                
    def _on_btn_clicked(self, widget, menu=None):
        menu.popup(None, None, None, 0, 0, None)

    def _on_cmd_clicked(self, widget, cmd=None):
        if cmd.has_key("title"):
            self.label.set_text(cmd["title"])

        if cmd.has_key("expect_key"):
            self.expect_key = cmd["expect_key"]
            self.expect_val = cmd["expect_val"]
        else:
            self.expect_key = ""
            self.expect_val = ""

        if cmd.has_key("cmd"):
            self.vte.feed_child(cmd["cmd"]+"\n")

    def _on_vte_button_press(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            if self.vte.get_has_selection():
                self.vte.copy_clipboard()
                self.vte.select_none()
            else:
                self.vte.paste_clipboard()
