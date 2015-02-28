#!/usr/bin/env python2
# -*- coding:utf8 -*-

import os
import os.path
import sys

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, Gtk, GObject, GdkPixbuf
from gi.repository.GdkPixbuf import Pixbuf

PATH_PLAGIN="plugins"
PATH_RES="res"
PATH_CONFIG=".jcm"

ICON_APP="app.png"

ICON_CLOSEALL = "close_all.png"
ICON_CLONE="clone.png"
ICON_CLOSE="close.png"

MENU_SIZE = 16

class TabHead(Gtk.HBox):
    def __init__(self, frame=None, title="", img=None, clone=True, close=True):
        Gtk.HBox.__init__(self, False, 0)

        self.frame = frame

        # icon
        if img != None and len(img) != 0:
            self.img = self.frame.load_img(img, MENU_SIZE);
            self.pack_start(self.img, False, False, 0)

        # title
        self.label = Gtk.Label(title)
        self.pack_start(self.label, False, False, 0)

        # clone button
        if clone:
            self.clone = Gtk.Button()
            self.clone.set_image(self.frame.load_img(ICON_CLONE, MENU_SIZE))
            self.clone.set_relief(Gtk.ReliefStyle.NONE)
            self.pack_start(self.clone, False, False, 0);

        # close button
        if close:
            self.close = Gtk.Button()
            self.close.set_image(self.frame.load_img(ICON_CLOSE, MENU_SIZE))
            self.close.set_relief(Gtk.ReliefStyle.NONE)
            self.pack_start(self.close, False, False, 0);

        self.show_all()

    def set_clone_clicked(self, cb):
        self.clone.connect("clicked", cb)

    def set_close_clicked(self, cb):
        self.close.connect("clicked", cb)

    def set_title(self, title):
        self.label.set_text(title)

class AbsTab:
    # 返回None说明是自动加载的Tab控件
    @staticmethod
    def get_type():abstract
    def __init__(self, frame):abstract
    def on_head(self):abstract # 获取tab头控件
    def on_body(self):abstract # 获取tab内容控件
    def on_focus(self):abstract
    def do_open(self, cfg):abstract
    def do_close(self):abstract # return: True 已正常关闭，False此Tab不支持关闭

class Frame:
    def __init__(self, title, version, cwd):
        Gdk.threads_init()

        self.path = cwd
        self.path_res = self.path + "/" + PATH_RES
        self.path_plugin = self.path + "/" + PATH_PLAGIN
        self.path_config = os.getenv("HOME") + "/" + PATH_CONFIG

        if os.path.exists(self.path_config) == False:
            os.mkdir(self.path_config)
        elif os.path.isdir(self.path_config) == False:
            print "[ERROR] " + self.path_config + " is not a direcotry !"
            sys.exit(-1)

        # application
        self.app = Gtk.Application.new("juniu.jcm", 0)

        # window
        self.window = Gtk.ApplicationWindow(Gtk.WindowType.TOPLEVEL)
        self.window.set_icon_from_file(self.path_res + "/" + ICON_APP)
        self.window.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.window.set_default_size(500, 400)
        #self.window.set_decorated(False)
        self.window.maximize()
        self.window.set_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.window.connect('key-press-event', self._on_window_key_press)
        self.window.connect('delete-event',self._on_window_delete_event)

        self._header_bar(title + " " + version)
        self.window.set_titlebar(self.header)

        self._notebook()

    def _header_bar(self, title):
        self.header = Gtk.HeaderBar()
        self.header.set_title(title)
        self.header.set_show_close_button(True)

        # close all tabs
        item = Gtk.Button()
        item.set_image(self.load_img("clean.svg", MENU_SIZE));
        item.connect("clicked", self._on_close_all_tabs_clicked)

        is_ubuntu = False
        for s in os.uname():
            if s.lower().find("ubuntu") != -1:
                is_ubuntu = True

        # 在Ubuntu系统中将'close all tabs'放在右侧
        if is_ubuntu:
            self.header.pack_end(item)
        else:
            self.header.pack_start(item)
        self.header.show_all()

    def _notebook(self):
        self.notebook = Gtk.Notebook()
        self.notebook.set_show_border(True)
        self.notebook.set_show_tabs(True)
        self.window.add(self.notebook)

    def load_pixbuf(self, name, size=None):
        fname = self.path_res + "/" + name
        pixbuf = Pixbuf.new_from_file(fname)
        if size != None:
            return pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.HYPER)
        return pixbuf

    def load_img(self, name, size=None):
        pixbuf = self.load_pixbuf(name, size)
        return Gtk.Image.new_from_pixbuf(pixbuf)
    
    def load_plugins(self):
        self.mod = {}
        sys.path.append(self.path_plugin)

        for n in os.listdir(self.path_plugin):
            if n[-3:] != ".py":
                continue
            name = n[0:-3]

            # 装载模块，获得类句柄
            mod = __import__(name)
            clazz = getattr(mod, name)

            # 获得插件类型
            t = clazz.get_type()

            # type != None 为协议类型插件，需要时再创建此类对象。
            if t != None:
                if self.mod.has_key(t):
                    print "Type Conflict: %s: %s and %s" % (t, str(clazz), str(self.mod[t]))
                    continue;
                self.mod[t] = clazz
            # type == None的插件是自动加载插件。
            else:
                tab = clazz(self)
                self.add_tab(tab)
                tab.do_open(None)

    def loop(self):
        self.window.show_all()
        Gtk.main()
    
    def add_tab(self, tab, focus=True, reorderable=True):
        if isinstance(tab, AbsTab) == False:
            return -1

        ret = self.notebook.append_page(tab.on_body(), tab.on_head())
        self.notebook.set_tab_reorderable(tab.on_body(), reorderable)
        self.notebook.show_all()
        self.window.show_all()

        page = self.notebook.get_nth_page(ret)
        setattr(page, "tab", tab)

        if focus:
            self.notebook.set_current_page(ret)

        return ret
    
    def del_tab(self, tab):
        n = self.notebook.page_num(tab.on_body())
        if n != -1:
            self.notebook.remove_page(n)
    
    def quit(self, ask):
        if ask == False:
            Gtk.quit_main()
            return False

        dlg = Gtk.MessageDialog(self.window,
                                Gtk.DialogFlags.MODAL,
                                Gtk.MessageType.QUESTION,
                                Gtk.ButtonsType.YES_NO,
                                "Quit ?")
        ret = dlg.run()
        if ret == Gtk.ResponseType.YES:
            dlg.destroy()
            Gtk.main_quit()
            return False
        else:
            dlg.destroy()
            return True

    def _close_all(self):
        num = self.notebook.get_n_pages()
        i = 0
        while i < num:
            page = self.notebook.get_nth_page(i)
            tab = getattr(page, "tab")
            if tab.do_close() == True:
                num = self.notebook.get_n_pages()
                i = 0
            else:
                i += 1

    def _on_close_all_tabs_clicked(self, widget, data=None):
        dlg = Gtk.MessageDialog(self.window,
                                Gtk.DialogFlags.MODAL,
                                Gtk.MessageType.QUESTION,
                                Gtk.ButtonsType.YES_NO,
                                "Close All Tabs?")
        ret = dlg.run()
        if ret == Gtk.ResponseType.YES:
            dlg.destroy()
            self._close_all()
            return False
        else:
            dlg.destroy()
            return True

    def _on_window_delete_event(self, widget, data=None):
        return self.quit(True)

    def _on_window_key_press(self, widget, event):
        # 快捷键 Ctrl + xxx
        if (event.state & Gdk.ModifierType.CONTROL_MASK) == Gdk.ModifierType.CONTROL_MASK:
            if event.keyval == Gdk.KEY_Right or event.keyval == Gdk.KEY_Page_Down:
                num = self.notebook.get_current_page() + 1
                count = self.notebook.get_n_pages()
                if num >= count:
                    num = 0;
                self.notebook.set_current_page(num)
                return True
            if event.keyval == Gdk.KEY_Left or event.keyval == Gdk.KEY_Page_Up:
                num = self.notebook.get_current_page() - 1
                count = self.notebook.get_n_pages()
                if num < 0:
                    num = count - 1
                self.notebook.set_current_page(num)
                return True

        # 任何按键输入后，焦点切换到指定控件。
        num = self.notebook.get_current_page()
        page = self.notebook.get_nth_page(num)
        tab = getattr(page, "tab")
        if tab != None:
            tab.on_focus()
        return False

    def run(self, cfg):
        t = cfg["type"]
        if self.mod.has_key(t):
            obj = self.mod[t](self)
            self.add_tab(obj)
            obj.do_open(cfg)
        else:
            print "[ER] type %s is not found" % t
