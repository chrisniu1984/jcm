# -*- coding:utf-8 -*-

import os
import shutil

import gobject
import gtk
import vte

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

class SiteTab(Frame.AbsTab):
    @staticmethod
    def get_type():
        # None 是自动加载插件。
        return None

    def __init__(self, frame):
        self.frame = frame
        self.config = frame.path_config + "/" + SITEFILE
        self.img = {}

        self.img["dir"] = gtk.gdk.pixbuf_new_from_file(self.frame.path_res + "/" + IMG_DIR)
        self.img["site"] = gtk.gdk.pixbuf_new_from_file(self.frame.path_res + "/" + IMG_SITE)
        self.img["shell"] = gtk.gdk.pixbuf_new_from_file(self.frame.path_res + "/" + IMG_SHELL)
        self.img["ssh"] = gtk.gdk.pixbuf_new_from_file(self.frame.path_res + "/" + IMG_SSH)

        # head
        self.label = gtk.Label("Site List")

        # body
        self.vbox = gtk.VBox(False, 0)
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
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_BOTH);
        self.vbox.pack_start(self.toolbar, False, False, 0)

        # quit
        item = gtk.ToolButton(gtk.image_new_from_file(self.frame.path_res + "/quit.png"), "Quit")
        self.toolbar.insert(item, -1)
        item.connect("clicked", self._on_quit_clicked)

        # close all
        item = gtk.ToolButton(gtk.image_new_from_file(self.frame.path_res + "/" + IMG_CLOSEALL), "Close All")
        self.toolbar.insert(item, -1)
        item.connect("clicked", self._on_close_all_clicked)

        # |
        item = gtk.SeparatorToolItem()
        self.toolbar.insert(item, -1)

        # reload
        item = gtk.ToolButton(gtk.image_new_from_file(self.frame.path_res + "/" + IMG_RELOAD), "Reload Config")
        self.toolbar.insert(item, -1)
        item.connect("clicked", self._on_reload_clicked)

        # reload
        item = gtk.ToolButton(gtk.image_new_from_file(self.frame.path_res + "/" + IMG_EDIT), "Edit Config")
        self.toolbar.insert(item, -1)
        item.connect("clicked", self._on_edit_clicked)

        # |
        item = gtk.SeparatorToolItem()
        self.toolbar.insert(item, -1)

        # help
        item = gtk.ToolButton(gtk.image_new_from_file(self.frame.path_res + "/" + IMG_HELP), "Help")
        self.toolbar.insert(item, -1)

        # About
        item = gtk.ToolButton(gtk.image_new_from_file(self.frame.path_res + "/" + IMG_ABOUT), "About")
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

    def _append_node(self, xml_node, parent):
        if xml_node.tag == "root":
            for child in xml_node:
                self._append_node(child, parent)

        elif xml_node.tag == "dir":
            p = self.treestore.append(parent, [self.img["dir"], xml_node.attrib["name"], None]);
            for child in xml_node:
                self._append_node(child, p)

        elif xml_node.tag == "site":
            cfg = xml_node.attrib.copy()

            cfg["extra"] = []
            for c in xml_node:
                if c.tag != "btn":
                    continue
                btn = []
                btn.append(c.attrib["name"])
                for cc in c:
                    if cc.tag != "cmd":
                        continue
                    btn.append(cc.attrib.copy())
                cfg["extra"].append(btn)

            img = self.img["site"]
            if cfg.has_key("type") and self.img.has_key(cfg["type"]):
                img = self.img[cfg["type"]]
            p = self.treestore.append(parent, [img, cfg["name"], cfg])
            #print cfg

    def _treestore(self):
        self.treestore = gtk.TreeStore(gtk.gdk.Pixbuf, gobject.TYPE_STRING, object)
        self._on_reload_clicked(None)

    def _treeview(self):
        self.treeview = gtk.TreeView()
        self.treeview.set_model(self.treestore)
        self.vbox.pack_start(self.treeview, True, True, 0)

        self.treeview.set_headers_visible(False)
        self.treeview.connect("row-activated", self._on_treeview_row_activated)
        sel = self.treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)

        col = gtk.TreeViewColumn()
        col.set_title("Site List");
        self.treeview.append_column(col);

        renderer = gtk.CellRendererPixbuf();
        col.pack_start(renderer, False);
        col.add_attribute(renderer, "pixbuf", COL_PIXBUF);

        renderer = gtk.CellRendererText();
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
