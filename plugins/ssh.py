# -*- coding:utf-8 -*-

import os
import signal

from gi.repository import Gdk, Gtk, GObject, Vte
from gi.repository.GdkPixbuf import Pixbuf

from NIU import Frame, AbsTab, TabHead, Term, Expect, Misc

MENU_SIZE = 16

class ssh(AbsTab):
    def __init__(self, frame):
        self.frame = frame
        self.cfg = None

        # head
        self.head = TabHead(frame, img="ssh.png")
        self.head.set_clone_clicked(self.__on_clone_clicked)
        self.head.set_close_clicked(self.__on_close_clicked)

        # body
        self.vbox = Gtk.VBox(False, 0)

        # menu
        self.menubar = Gtk.MenuBar()
        self.vbox.pack_start(self.menubar, False, False, 0)
        self.vbox.show_all()

        # term
        self.term = Term()
        self.term.SET_TITLE_CHANGED(self.__on_title_changed);
        self.term.connect("child-exited", self.__on_child_exited)
        self.vbox.pack_start(self.term, True, True, 0)
        self.vbox.show_all()

        self.cwd = "~"

    def HEAD(self):
        return self.head

    def BODY(self):
        return self.vbox

    def on_focus(self):
        self.term.grab_focus()

    def _extra_menu(self, cfg_menu, parent=None):
        if cfg_menu["__NAME__"] != "menu":
            return

        # new menu-item, add it to parent
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

    def on_open(self, cfg):
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

        self.head.set_title("  " + cfg["name"] + " ")
        cmd = ['/usr/bin/ssh', cfg["user"] + "@" + cfg["host"], "-p", cfg["port"]]

        self.childpid = self.term.RUN(cmd)

        if self.childpid != None:
            self.term.connect("child-exited", self.__on_child_exited)

    def on_close(self):
        if self.childpid > 0:
            os.kill(self.childpid, signal.SIGKILL)
            self.childpid = 0

        self.frame.del_tab(self)
        return True

    def __on_child_exited(self, widget, stat):
        self.childpid = 0
        self.on_close()

    def __on_clone_clicked(self, widget, data=None):
        self.frame.run(self.cfg)

    def __on_close_clicked(self, widget, data=None):
        self.on_close()

    def __on_execute_clicked(self, widget, val):
        uri = val
        if uri.find("#URI#") != -1:
            s = "sftp://#USER#:#PASS#@#HOST#:#PORT##CWD#"
            uri = uri.replace("#URI#", s)

        uri = uri.replace("#USER#", self.cfg["user"])
        uri = uri.replace("#PASS#", self.cfg["pass"])
        uri = uri.replace("#HOST#", self.cfg["host"])
        uri = uri.replace("#PORT#", self.cfg["port"])
        uri = uri.replace("#CWD#",  self.cwd)

        Misc.execute(uri)

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

    def __on_title_changed(self, title):
        idx = title.find(":")
        if idx != -1:
            self.cwd = title[idx+1:].strip()

        if self.cwd.startswith("~"):
            prefix = "/root"
            if self.cfg["user"] != "root":
                prefix = "/home/" + self.cfg["user"] + "/"
            self.cwd = prefix + self.cwd[1:]
