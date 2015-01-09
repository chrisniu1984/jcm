# -*- coding:utf-8 -*-

import os
import shutil

from gi.repository import Gdk, Gtk, GObject
from gi.repository.GdkPixbuf import Pixbuf

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import Frame

SITEFILE = "site.xml"

IMG_DIR = "dir.png"
IMG_SITE = "site.png"
IMG_SHELL = "shell.png"
IMG_SSH = "ssh.png"

IMG_QUIT = "quit.png"
IMG_CLOSEALL = "close_all.png"
IMG_RELOAD = "reload.png"
IMG_EDIT = "edit.png"
IMG_HELP = "help.png"
IMG_ABOUT = "about.png"

COL_PIXBUF = 0
COL_NAME   = 1
COL_CFG    = 2

PIXBUF_SIZE = 32
IMG_SIZE = 32

class SiteTab(Frame.AbsTab):
    @staticmethod
    def get_type():
        # None 是自动加载插件。
        return None

    def __init__(self, frame):
        self.frame = frame
        self.config = frame.path_config + "/" + SITEFILE
        self.img = {}

        self.img["dir"]     = self.frame.load_pixbuf(IMG_DIR, PIXBUF_SIZE)
        self.img["site"]    = self.frame.load_pixbuf(IMG_SITE, PIXBUF_SIZE)
        self.img["shell"]   = self.frame.load_pixbuf(IMG_SHELL, PIXBUF_SIZE)
        self.img["ssh"]     = self.frame.load_pixbuf(IMG_SSH, PIXBUF_SIZE)

        # head
        self.label = Gtk.Label("Site List")

        # body
        self.vbox = Gtk.VBox(False, 0)
        self._toolbar()
        self._treestore()
        self._treeview()

    def head(self):
        return self.label

    def body(self):
        return self.vbox

    def focus(self):
        self.treeview.grab_focus();

    def open(self, cfg):
        pass

    def close(self):
        return False

    def _toolbar(self):
        self.toolbar = Gtk.Toolbar()
        self.toolbar.set_style(Gtk.ToolbarStyle.BOTH)
        self.vbox.pack_start(self.toolbar, False, False, 0)

        # quit
        item = Gtk.ToolButton()
        item.set_label("Quit")
        item.set_icon_widget(self.frame.load_img(IMG_QUIT, IMG_SIZE))
        item.connect("clicked", self._on_quit_clicked)
        self.toolbar.insert(item, -1)

        # close all
        item = Gtk.ToolButton()
        item.set_label("Close All")
        item.set_icon_widget(self.frame.load_img(IMG_CLOSEALL, IMG_SIZE))
        item.connect("clicked", self._on_close_all_clicked)
        self.toolbar.insert(item, -1)

        # |
        item = Gtk.SeparatorToolItem()
        self.toolbar.insert(item, -1)

        # reload config
        item = Gtk.ToolButton()
        item.set_label("Reload Config")
        item.set_icon_widget(self.frame.load_img(IMG_RELOAD, IMG_SIZE))
        item.connect("clicked", self._on_reload_clicked)
        self.toolbar.insert(item, -1)

        # edit config
        item = Gtk.ToolButton()
        item.set_label("Edit Config")
        item.set_icon_widget(self.frame.load_img(IMG_EDIT, IMG_SIZE))
        item.connect("clicked", self._on_edit_clicked)
        self.toolbar.insert(item, -1)

        # |
        item = Gtk.SeparatorToolItem()
        self.toolbar.insert(item, -1)

        # help
        item = Gtk.ToolButton()
        item.set_label("Help")
        item.set_icon_widget(self.frame.load_img(IMG_HELP, IMG_SIZE))
        self.toolbar.insert(item, -1)

        # About
        item = Gtk.ToolButton()
        item.set_label("About")
        item.set_icon_widget(self.frame.load_img(IMG_ABOUT, IMG_SIZE))
        self.toolbar.insert(item, -1)

    def _on_quit_clicked(self, widget, data=None):
        self.frame.quit(True)

    def _on_close_all_clicked(self, widget, data=None):
        self.frame.close_all(True)

    def _on_reload_clicked(self, widget, data=None):
        if os.path.exists(self.config) == False:
            shutil.copyfile(self.frame.path_example + "/site.xml", self.config)

        if os.access(self.config, os.R_OK):
            self.treestore.clear()
            root = ET.ElementTree(file=self.config).getroot()
            self._append_node(root, None)

    def _on_edit_clicked(self, widget, data=None):
        os.system("gvim " + self.config)

    def _cfg_extra(self, xml_node):
        name = xml_node.tag;
        attr = xml_node.attrib.copy();
        lst = []
        for child in xml_node:
            lst.append(self._cfg_extra(child))

        return {"__NAME__":name, "__ATTR__" : attr, "__CHILDREN__":lst}

    def _append_node(self, xml_node, parent):
        if xml_node.tag == "root":
            for child in xml_node:
                self._append_node(child, parent)

        elif xml_node.tag == "dir":
            p = self.treestore.append(parent, [self.img["dir"], xml_node.attrib["name"], None]);
            for child in xml_node:
                self._append_node(child, p)

        elif xml_node.tag == "site":
            cfg = xml_node.attrib.copy() # 当前元素所有属性通过字典方式存储
            cfg["__EXTRA__"] = [] # 子节点通过数组方式存储,_每个成员格式为 {NAME, ATTR, CHILDREN}。
            for c in xml_node:
                cfg["__EXTRA__"].append(self._cfg_extra(c));

            img = self.img["site"]
            if cfg.has_key("type") and self.img.has_key(cfg["type"]):
                img = self.img[cfg["type"]]
            p = self.treestore.append(parent, [img, cfg["name"], cfg])
            # print cfg

    def _treestore(self):
        self.treestore = Gtk.TreeStore(Pixbuf, GObject.TYPE_STRING, object)
        self._on_reload_clicked(None)

    def _treeview(self):
        self.treeview = Gtk.TreeView()
        self.treeview.set_model(self.treestore)
        self.vbox.pack_start(self.treeview, True, True, 0)

        self.treeview.set_headers_visible(False)
        self.treeview.connect("row-activated", self._on_treeview_row_activated)
        sel = self.treeview.get_selection().set_mode(Gtk.SelectionMode.SINGLE)

        col = Gtk.TreeViewColumn()
        col.set_title("Site List");
        self.treeview.append_column(col);

        renderer = Gtk.CellRendererPixbuf();
        col.pack_start(renderer, False);
        col.add_attribute(renderer, "pixbuf", COL_PIXBUF);

        renderer = Gtk.CellRendererText();
        col.pack_start(renderer, False);
        col.add_attribute(renderer, "text", COL_NAME);

    def _on_treeview_row_activated(self, widget, path, data=None):
        it = self.treestore.get_iter(path)
        cfg = self.treestore.get_value(it, COL_CFG)
        if cfg == None:
            if self.treeview.row_expanded(path):
                self.treeview.collapse_row(path)
            else:
                self.treeview.expand_to_path(path)
            return

        self.frame.run(cfg)
