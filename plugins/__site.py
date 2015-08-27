# -*- coding:utf-8 -*-

import os
import shutil

from gi.repository import Gdk, Gtk, GObject
from gi.repository.GdkPixbuf import Pixbuf

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from NIU import Frame, AbsTab, TabHead, Term, Expect, Misc

SITEFILE = "site.xml"

IMG_DIR = "dir.png"
IMG_SITE = "site.png"
IMG_SHELL = "shell.png"
IMG_SSH = "ssh.png"

IMG_RELOAD = "reload.png"
IMG_EDIT = "edit.png"

COL_PIXBUF = 0
COL_NAME   = 1
COL_CFG    = 2

class __site(AbsTab):
    def __init__(self, frame):
        self.frame = frame
        self.config = frame.path_config + "/" + SITEFILE

        # img
        self.img = {}
        self.img["dir"]     = self.frame.load_pixbuf(IMG_DIR, 24)
        self.img["site"]    = self.frame.load_pixbuf(IMG_SITE)
        self.img["shell"]   = self.frame.load_pixbuf(IMG_SHELL, 24)
        self.img["ssh"]     = self.frame.load_pixbuf(IMG_SSH, 24)

        # head
        self.head = TabHead(frame, title="Site List", close=False)

        # body
        self.__init_treestore()
        self.__init_treeview()

    def HEAD(self):
        return self.head

    def BODY(self):
        return self.treeview

    def HBAR(self):
        if not hasattr(self, "hbar"):
            self.hbar = Gtk.HBox()

            # reload config
            item = Gtk.Button()
            item.set_tooltip_text("Reload Config")
            item.set_relief(Gtk.ReliefStyle.NONE)
            item.set_image(self.frame.load_icon(IMG_RELOAD))
            item.connect("clicked", self.__on_reload_clicked)
            self.hbar.pack_start(item, False, False, 0)

            # edit config
            item = Gtk.Button()
            item.set_tooltip_text("Edit Config")
            item.set_relief(Gtk.ReliefStyle.NONE)
            item.set_image(self.frame.load_icon(IMG_EDIT))
            item.connect("clicked", self.__on_edit_clicked)
            self.hbar.pack_start(item, False, False, 0)

        return self.hbar

    def on_focus(self):
        self.treeview.grab_focus();

    def on_open(self, cfg):
        pass

    def __init_treestore(self):
        self.treestore = Gtk.TreeStore(Pixbuf, GObject.TYPE_STRING, object)
        self.__reload_cfg()

    def __init_treeview(self):
        self.treeview = Gtk.TreeView()
        self.treeview.set_model(self.treestore)

        self.treeview.set_headers_visible(False)
        self.treeview.connect("row-activated", self.__on_treeview_row_activated)
        sel = self.treeview.get_selection().set_mode(Gtk.SelectionMode.SINGLE)

        col = Gtk.TreeViewColumn()
        self.treeview.append_column(col);

        renderer = Gtk.CellRendererPixbuf();
        col.pack_start(renderer, False);
        col.add_attribute(renderer, "pixbuf", COL_PIXBUF);

        renderer = Gtk.CellRendererText();
        col.pack_start(renderer, False);
        col.add_attribute(renderer, "text", COL_NAME);


    def __on_treeview_row_activated(self, widget, path, data=None):
        it = self.treestore.get_iter(path)
        cfg = self.treestore.get_value(it, COL_CFG)
        if cfg == None:
            if self.treeview.row_expanded(path):
                self.treeview.collapse_row(path)
            else:
                self.treeview.expand_to_path(path)
            return

        self.frame.run(cfg)

    def __on_reload_clicked(self, widget, data=None):
        self.__reload_cfg()

    def __on_edit_clicked(self, widget, data=None):
        #os.system("gvim " + self.config)
        Misc.execute("xdg-open " + self.config)

    def __cfg_extra(self, xml_node):
        name = xml_node.tag;
        attr = xml_node.attrib.copy();
        lst = []
        for child in xml_node:
            lst.append(self.__cfg_extra(child))

        return {"__NAME__":name, "__ATTR__" : attr, "__CHILDREN__":lst}

    def __append_node(self, xml_node, parent):
        if xml_node.tag == "root":
            for child in xml_node:
                self.__append_node(child, parent)

        elif xml_node.tag == "dir":
            p = self.treestore.append(parent, [self.img["dir"], xml_node.attrib["name"], None]);
            for child in xml_node:
                self.__append_node(child, p)

        # xml中每个site元素都会生成一个字段对象cfg，cfg对象的具体结构如下：
        # 1、site元素的所有属性都通过字典方式存储到cfg对象中。其中我只关心属性name和type，其他本大爷不关心。
        # 2、cfg中有个特殊的key叫做"__EXTRA__"，其值是个数组。用来存储site下的所有子节点。
        #    数组中每个成员格式为字典： {__NAME__, __ATTR__, __CHILDREN__}。
        #    其中的__CHILDREN__又是一个数组，与本节点存储方式相同。
        elif xml_node.tag == "site":
            cfg = xml_node.attrib.copy() # 当前元素所有属性通过字典方式存储
            cfg["__EXTRA__"] = []
            for c in xml_node:
                cfg["__EXTRA__"].append(self.__cfg_extra(c));

            img = self.img["site"]
            if cfg.has_key("type") and self.img.has_key(cfg["type"]):
                img = self.img[cfg["type"]]
            p = self.treestore.append(parent, [img, cfg["name"], cfg])
            # print cfg

    def __reload_cfg(self):
        if os.path.exists(self.config) == False:
            shutil.copyfile(self.frame.path_example + "/site.xml", self.config)

        if os.access(self.config, os.R_OK):
            self.treestore.clear()
            root = ET.ElementTree(file=self.config).getroot()
            self.__append_node(root, None)

