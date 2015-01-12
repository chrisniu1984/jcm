# -*- coding:utf-8 -*-

import os
import signal

from gi.repository import Gdk, Gtk, GObject, Vte
from gi.repository.GdkPixbuf import Pixbuf

import Frame

IMG_CLOSE="close.svg"

MENU_SIZE = 16

class EXPECT:
    def __init__(self, hint, val, once=False, item=None):
        self.hint = hint
        self.val = val
        self.once = once
        self.item = item

    @staticmethod
    def new_from_cfg(cfg_expect, item=None):
        if cfg_expect["__NAME__"] != "expect":
            return
        attr = cfg_expect["__ATTR__"]

        once = False
        if attr.has_key("once") and attr["once"] == "true":
            once = True

        return EXPECT(attr["hint"], attr["input"], once, item)

class SshTab(Frame.AbsTab):
    @staticmethod
    def get_type():
        return "ssh";

    def __init__(self, frame):
        self.frame = frame
        self.expect = {} # hint -> EXPECT
        self.last_text = ""

        # head
        self.hbox = Gtk.HBox(False, 0)

        self.label = Gtk.Label("")
        self.hbox.pack_start(self.label, False, False, 0)
        self.button = Gtk.Button()
        self.button.set_image(self.frame.load_img(IMG_CLOSE, 16))
        self.button.set_relief(Gtk.ReliefStyle.NONE)
        self.button.connect("clicked", self._on_close_clicked, None)

        self.hbox.pack_start(self.button, False, False, 0);
        self.hbox.show_all()

        # body
        self.vbox = Gtk.VBox(False, 0)

        self.menubar = Gtk.MenuBar()
        self.vbox.pack_start(self.menubar, False, False, 0)
        self.vbox.show_all()

        self.term = Vte.Terminal()
        #self.term.set_font_from_string("WenQuanYi Micro Hei Mono 11");
        self.term.set_scrollback_lines(1024);
        self.term.set_scroll_on_keystroke(1);
        self.term.connect("button-press-event", self._on_term_button_press);
        self.vbox.pack_start(self.term, True, True, 0)
        self.vbox.show_all()

    def head(self):
        return self.hbox

    def body(self):
        return self.vbox

    def focus(self):
        self.term.grab_focus()

    def _extra_menu(self, cfg_menu, parent=None):
        if cfg_menu["__NAME__"] != "menu":
            return

        # new menu-item, add this to parent
        menuitem = Gtk.ImageMenuItem(cfg_menu["__ATTR__"]["name"])
        menuitem.set_always_show_image(True)

        if parent == None:
            menuitem.set_image(self.frame.load_img("menu.png", MENU_SIZE))
            self.menubar.append(menuitem)
        else:
            menuitem.set_image(self.frame.load_img("submenu.png", MENU_SIZE))
            parent.append(menuitem)

        # new sub-menu for menu-item
        submenu = Gtk.Menu()
        menuitem.set_submenu(submenu)

        # add more menu-item to sub-menu
        for cfg_item in cfg_menu["__CHILDREN__"]:
            attr = cfg_item["__ATTR__"]

            if cfg_item["__NAME__"] == "menu":
                self._extra_menu(cfg_item, submenu)

            elif cfg_item["__NAME__"] == "input":
                item = Gtk.ImageMenuItem(attr["name"]);
                item.set_always_show_image(True)
                item.set_image(self.frame.load_img("input.png", MENU_SIZE))
                item.connect("activate", self._on_menu_input_clicked, cfg_item);
                submenu.append(item)

            elif cfg_item["__NAME__"] == "execute":
                item = Gtk.ImageMenuItem(attr["name"]);
                item.set_always_show_image(True)
                item.set_image(self.frame.load_img("execute.png", MENU_SIZE))
                item.connect("activate", self._on_execute_clicked, attr["val"]);
                submenu.append(item)

            elif cfg_item["__NAME__"] == "expect":
                item = Gtk.CheckMenuItem(attr["name"]);

                expect = EXPECT.new_from_cfg(cfg_item, item)

                if attr.has_key("check") and attr["check"] == "true":
                    item.set_active(True)
                    self.expect[expect.hint] = expect

                setattr(item, "expect", expect)
                item.connect("activate", self._on_menu_expect_clicked);
                submenu.append(item)

        submenu.show_all()

    def _extra_expect(self, cfg_expect):
        expect = EXPECT.new_from_cfg(cfg_expect)
        if expect == None:
            return
        self.expect[expect.hint] = expect

    def open(self, cfg):
        self.cfg = cfg

        # 处理__EXTRA__
        for e in cfg["__EXTRA__"]:
            if e["__NAME__"] == "menu":
                self._extra_menu(e)
                self.menubar.show_all()
            elif e["__NAME__"] == "execute":
                self.frame.execute(e["__ATTR__"]["val"]);
            elif e["__NAME__"] == "expect":
                self._extra_expect(e)

        # auto add expect for login
        if cfg.has_key("pass"):
            self.expect["password:"] = EXPECT("password:", cfg["pass"], True)

        self.term.feed("connecting ... " + cfg["host"] + ":" + cfg["port"] + "\r\n")
        self.term.feed("\n")

        self.label.set_text(cfg["name"])
        cmd = ['/usr/bin/ssh', cfg["user"] + "@" + cfg["host"], "-p", cfg["port"]]

        self.childpid = self.term.spawn_sync(Vte.PtyFlags.DEFAULT, os.getcwd(),
                            cmd, None, GObject.SPAWN_SEARCH_PATH, None, None)[1]

        if self.childpid > 0:
            self.term.connect('child-exited', self._on_child_exited)
            self.term.connect('contents-changed', self._on_contents_changed)

    def close(self):
        if self.childpid > 0:
            os.kill(self.childpid, signal.SIGKILL)
            self.childpid = 0

        self.frame.del_tab(self)
        return True

    def _on_child_exited(self, widget, x):
        self.childpid = 0
        self.close()

    def _on_close_clicked(self, widget, data=None):
        self.close()

    def _on_contents_changed(self, widget, data=None):
        text = self.term.get_text(None)[0].strip()
        if text == self.last_text:
            return
        self.last_text = text

        # expect
        for k,e in self.expect.items():
            if text.endswith(k):
                self.term.feed_child(e.val + "\n", -1)
                if e.once:
                    if e.item != None:
                        e.item.set_active(False)
                    else:
                        del self.expect[k]
                return

    def _on_execute_clicked(self, widget, val):
        self.frame.execute(val)
        #os.system(val)

    def _on_menu_input_clicked(self, widget, cfg_input=None):
        attr = cfg_input["__ATTR__"]

        # is this expect?
        if attr.has_key("expect_hint"):
            self.expect[attr["expect_hint"]] = EXPECT(attr["expect_hint"], attr["expect_input"], True)

        if attr.has_key("input"):
            self.term.feed_child(attr["input"]+"\n", -1)

    def _on_menu_expect_clicked(self, widget, expect=None):
        expect = getattr(widget, "expect")
        if widget.get_active() == True:
            self.expect[expect.hint] = expect
        else:
            del self.expect[expect.hint]

    def _on_term_button_press(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            if self.term.get_has_selection():
                self.term.copy_clipboard()
                self.term.select_none()
            else:
                self.term.paste_clipboard()
