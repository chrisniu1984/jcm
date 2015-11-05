#!/usr/bin/env python2
# -*- coding:utf8 -*-

import os
import os.path
import sys

import gi
gi.require_version("GObject", "2.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Gdk, Gtk, GObject, GdkPixbuf
from gi.repository.GdkPixbuf import Pixbuf

PATH_PLAGIN="plugins"
PATH_RES="res"
PATH_CONFIG=".jcm"

ICON_APP="app.png"
ICON_CLOSEALL = "close_all.png"
ICON_CLOSE="close.png"

MENU_SIZE = 24

class TabHead(Gtk.HBox):
    def __init__(self, frame=None, title="", img=None, close=True):
        Gtk.HBox.__init__(self, False, 0)

        self.frame = frame

        # icon
        if img != None and len(img) != 0:
            self.icon = self.frame.load_img(img, MENU_SIZE)
            self.pack_start(self.icon, False, False, 0)

        # title
        self.label = Gtk.Label()
        self.pack_start(self.label, False, False, 0)

        # menu label for popup
        self.menu = Gtk.HBox()
        if img != None and len(img) != 0:
            self.menu_icon = self.frame.load_img(img, MENU_SIZE)
            self.menu.pack_start(self.menu_icon, False, False, 0)
        self.menu_label = Gtk.Label(title)
        self.menu.pack_start(self.menu_label, False, False, 0)
        self.menu.show_all()

        # entry for change title
        self.entry = Gtk.Entry();
        self.entry.set_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.entry.connect('key-press-event', self.__on_entry_key_press)
        self.entry.set_has_frame(False)
        self.pack_start(self.entry, False, False, 0);

        # close button
        if close:
            self.close = Gtk.Button()
            self.close.set_tooltip_text("Close")
            self.close.set_image(self.frame.load_img(ICON_CLOSE, MENU_SIZE))
            self.close.set_relief(Gtk.ReliefStyle.NONE)
            self.pack_start(self.close, False, False, 0);

        self.set_title(title)

        self.show_all()
        self.entry.hide()


    def show_entry(self):
        if self.entry.is_visible() == False:
            self.entry.set_text(self.label.get_text().strip())
            self.entry.show()
            self.label.hide()
            self.entry.grab_focus();

    def __on_entry_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Return:
            self.entry.hide()
            self.set_title(self.entry.get_text())
            self.label.show()
            return True

        elif event.keyval == Gdk.KEY_Escape:
            self.entry.hide()
            self.label.show()
            return True

        return False

    def set_close_clicked(self, cb):
        if self.close != None:
            self.close.connect("clicked", cb)

    def set_title(self, title):
        t = " " + title + " "
        self.label.set_text(t)
        self.menu_label.set_text(t)

    def get_menu(self):
        return self.menu

class AbsTab:
    def __init__(self, frame):abstract
    def HEAD(self):abstract # 获取tab头控件
    def BODY(self):abstract # 获取tab内容控件

    def HBAR(self):
        return None

    def on_focus(self):
        pass

    def on_open(self, cfg):abstract
    def on_close(self):
        return False

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
        #self.window.set_decorated(False)
        self.window.maximize()
        self.window.set_default_size(400, 300)
        self.window.set_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.window.connect('key-press-event', self._on_window_key_press)
        self.window.connect('delete-event',self._on_window_delete_event)

        self.__init_header_bar(title + " " + version)
        self.__init_notebook()

    def __init_header_bar(self, title):
        self.header = Gtk.HeaderBar()
        self.header.set_title(title)
        self.header.set_show_close_button(True)

        # close all tabs
        item = Gtk.Button()
        item.set_tooltip_text("Close All Tabs")
        #sc = item.get_style_context()
        #style.bg[Gtk.StateType.PRELIGHT] = style.bg[Gtk.StateType.NORMAL]
        #item.set_style(style)
        item.set_image(self.load_img("clean.svg", MENU_SIZE));
        item.connect("clicked", self._on_close_all_tabs_clicked)
        self.header.pack_start(item)

        # custom toolbutton for tab
        item = Gtk.HBox()
        self.header_box = item
        self.header_item = None
        self.header.pack_start(item)

        self.header.show_all()
        self.window.set_titlebar(self.header)

    def __init_notebook(self):
        self.notebook = Gtk.Notebook()
        self.notebook.set_show_border(True)
        self.notebook.set_show_tabs(True)
        self.notebook.set_scrollable(True)
        self.notebook.popup_enable()
        self.notebook.connect("switch-page", self.__on_notebook_switched)
        self.window.add(self.notebook)

    def __update_header_bar(self, page_num):
        if page_num < 0:
            return
        page = self.notebook.get_nth_page(page_num)
        if not hasattr(page, "tab"):
            return

        # remove old
        if self.header_item != None:
            self.header_box.remove(self.header_item)
        self.header_item = None

        # add new
        tab = getattr(page, "tab")
        self.header_item = tab.HBAR()
        if self.header_item != None:
            self.header_box.pack_start(self.header_item, False, False, 0)
            self.header_box.show_all()

    def __on_notebook_switched(self, notebook, xxx, page_num):
        self.__update_header_bar(page_num)

    def load_pixbuf(self, name, size=None):
        fname = self.path_res + "/" + name
        pixbuf = Pixbuf.new_from_file(fname)
        if size != None:
            return pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.HYPER)
        return pixbuf

    def load_img(self, name, size=None):
        pixbuf = self.load_pixbuf(name, size)
        return Gtk.Image.new_from_pixbuf(pixbuf)

    def load_icon(self, name):
        pixbuf = self.load_pixbuf(name, MENU_SIZE)
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
            if name.startswith("__"):
                tab = clazz(self)
                self.add_tab(tab)
                tab.on_open(None)
            else:
                self.mod[name] = clazz

    def loop(self):
        self.window.show_all()
        Gtk.main()
    
    def add_tab(self, tab, focus=True, reorderable=True):
        if isinstance(tab, AbsTab) == False:
            return -1

        ret = self.notebook.append_page_menu(tab.BODY(), tab.HEAD(), tab.HEAD().get_menu())
        self.notebook.set_tab_reorderable(tab.BODY(), reorderable)
        self.notebook.show_all()
        self.window.show_all()

        page = self.notebook.get_nth_page(ret)
        setattr(page, "tab", tab)

        if focus:
            self.__update_header_bar(ret)
            self.notebook.set_current_page(ret)

        return ret
    
    def del_tab(self, tab):
        n = self.notebook.page_num(tab.BODY())
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
            if tab.on_close() == True:
                num = self.notebook.get_n_pages()
                i = 0
            else:
                i += 1

    def _on_filezilla_clicked(self, widget, data=None):
        i = self.notebook.get_current_page();
        page = self.notebook.get_nth_page(i)
        tab = getattr(page, "tab")
        if hasattr(tab, "on_filezilla"):
            tab.on_filezilla()
        else:
            print "no on_filezilla"

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

            elif event.keyval == Gdk.KEY_Left or event.keyval == Gdk.KEY_Page_Up:
                num = self.notebook.get_current_page() - 1
                count = self.notebook.get_n_pages()
                if num < 0:
                    num = count - 1
                self.notebook.set_current_page(num)
                return True

            elif event.keyval == Gdk.KEY_Up:
                num = self.notebook.get_current_page()
                page = self.notebook.get_nth_page(num)
                tab = getattr(page, "tab")
                if tab != None:
                    tab.HEAD().show_entry()
                return True

        # 任何按键输入后，焦点切换到指定控件。
        num = self.notebook.get_current_page()
        page = self.notebook.get_nth_page(num)
        tab = getattr(page, "tab")
        if tab != None and tab.HEAD().entry.is_visible() == False:
            tab.on_focus()
        return False

    def run(self, cfg):
        t = cfg["type"]
        if self.mod.has_key(t):
            obj = self.mod[t](self)
            self.add_tab(obj)
            obj.on_open(cfg)
        else:
            print "[ER] type %s is not found" % t
