# -*- coding:utf-8 -*-

import os
import signal

from gi.repository import Gdk, Gtk, GObject, Vte
from gi.repository.GdkPixbuf import Pixbuf

from NIU import Frame, AbsTab, Term, Expect

IMG_TYPE="ssh.png"
IMG_CLOSE="close.png"
IMG_CLONE="clone.png"

MENU_SIZE = 16

class SshTab(AbsTab):
    @staticmethod
    def get_type():
        return "ssh";

    def __init__(self, frame):
        self.frame = frame
        self.cfg = None

        # head
        self.hbox = Gtk.HBox(False, 0)
        self.img = self.frame.load_img(IMG_TYPE, MENU_SIZE);
        self.hbox.pack_start(self.img, False, False, 0)
        self.label = Gtk.Label("")
        self.hbox.pack_start(self.label, False, False, 0)

        self.clone = Gtk.Button()
        self.clone.set_image(self.frame.load_img(IMG_CLONE, 16))
        self.clone.set_relief(Gtk.ReliefStyle.NONE)
        self.clone.connect("clicked", self.__on_clone_clicked)
        self.hbox.pack_start(self.clone, False, False, 0);

        self.button = Gtk.Button()
        self.button.set_image(self.frame.load_img(IMG_CLOSE, 16))
        self.button.set_relief(Gtk.ReliefStyle.NONE)
        self.button.connect("clicked", self.__on_close_clicked, None)

        self.hbox.pack_start(self.button, False, False, 0);
        self.hbox.show_all()

        # body
        self.vbox = Gtk.VBox(False, 0)

        self.menubar = Gtk.MenuBar()
        self.vbox.pack_start(self.menubar, False, False, 0)
        self.vbox.show_all()

        self.term = Term()
        self.term.connect("child-exited", self.__on_child_exited)
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
                setattr(item, "__ATTR__", cfg_item["__ATTR__"])
                item.connect("activate", self.__on_menu_input_clicked);
                submenu.append(item)

            elif cfg_item["__NAME__"] == "execute":
                item = Gtk.ImageMenuItem(attr["name"]);
                item.set_always_show_image(True)
                item.set_image(self.frame.load_img("execute.png", MENU_SIZE))
                item.connect("activate", self.__on_execute_clicked, attr["val"]);
                submenu.append(item)

            elif cfg_item["__NAME__"] == "expect":
                item = Gtk.CheckMenuItem(attr["name"]);

                expect = Expect.new_from_dict(cfg_item["__ATTR__"], item)

                if attr.has_key("check") and attr["check"] == "true":
                    item.set_active(True)
                    self.term.expect[expect.hint] = expect

                setattr(item, "expect", expect)
                item.connect("activate", self.__on_menu_expect_clicked);
                submenu.append(item)

        submenu.show_all()

    def _extra_expect(self, cfg_expect):
        expect = Expect.new_from_dict(cfg_expect["__ATTR__"])
        if expect == None:
            return
        self.term.expect[expect.hint] = expect

    def open(self, cfg):
        self.cfg = cfg

        # 处理__EXTRA__
        for e in cfg["__EXTRA__"]:
            if e["__NAME__"] == "menu":
                self._extra_menu(e)
                self.menubar.show_all()
            elif e["__NAME__"] == "execute":
                a = e["__ATTR__"]
                if a.has_key("sync") and a["sync"] == 'true':
                    os.system(a["val"])
                else:
                    self.frame.execute(a["val"]);
            elif e["__NAME__"] == "expect":
                self._extra_expect(e)

        # auto add expect for login
        if cfg.has_key("pass"):
            self.term.expect["password:"] = Expect(hint="password:", val=cfg["pass"], once=True)

        self.term.feed("connecting ... " + cfg["host"] + ":" + cfg["port"] + "\r\n")
        self.term.feed("\n")

        self.label.set_text("  " + cfg["name"] + " ")
        cmd = ['/usr/bin/ssh', cfg["user"] + "@" + cfg["host"], "-p", cfg["port"]]

        self.childpid = self.term.RUN(cmd)

        if self.childpid != None:
            self.term.connect("child-exited", self.__on_child_exited)

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
        self.frame.run(self.cfg)

    def __on_close_clicked(self, widget, data=None):
        self.close()

    def __on_execute_clicked(self, widget, val):
        self.frame.execute(val)

    def __on_menu_input_clicked(self, widget):
        attr = getattr(widget, "__ATTR__")

        if attr.has_key("val"):
            # is there a Expect ?
            if attr.has_key("expect_hint"):
                self.term.expect[attr["expect_hint"]] = \
                    Expect(hint=attr["expect_hint"], val=attr["expect_input"], once=True)

            self.term.feed_child(attr["val"]+"\n", -1)

    def __on_menu_expect_clicked(self, widget, expect=None):
        expect = getattr(widget, "expect")
        if widget.get_active() == True:
            self.term.expect[expect.hint] = expect
        else:
            del self.term.expect[expect.hint]
