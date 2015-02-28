# -*- coding:utf-8 -*-

import os
from gi.repository import Gdk, Gtk, GObject, Vte

from expect import Expect

class Term(Vte.Terminal):
    def __init__(self):
        Vte.Terminal.__init__(self)

        self.set_scrollback_lines(1024)
        self.set_scroll_on_keystroke(True)
        self.set_rewrap_on_resize(True)
    
        # EXPECT
        self.last_text = ""
        self.expect = {} # hint -> EXPECT
    
        # CB
        self.call_title_changed = None

    def SET_TITLE_CHAGED(self, cb):
        self.call_title_changed = cb

    def RUN(self, cmd, cwd=None):
        if cwd == None:
            cwd = os.getcwd()

        if hasattr(self, "spawn_sync"):
            ret, child_pid = self.spawn_sync(Vte.PtyFlags.DEFAULT, cwd,
                                cmd, None, GObject.SPAWN_SEARCH_PATH, None, None)
        elif hasattr(term, "fork_command_full"):
            ret, child_pid = self.fork_command_full(Vte.PtyFlags.DEFAULT, cwd,
                                cmd, None, GObject.SPAWN_SEARCH_PATH, None, None)
    
        if ret == False:
            return None
        return child_pid

    def ADD_EXPECT(self, hint, val, once=False, checkMenuItem=None):
        self.expect[hint] = Expect(hint=hint, val=val, once=once, checkMenuItem=checkMenuItem)

    def ADD_EXPECT_BY_DICT(self, d, checkMenuItem=None):
        expect = Expect.new_from_dict(d, checkMenuItem)
        if expect != None:
            self.expect[expect.hint] = expect

    def DEL_EXPECT(self, hint):
        if self.expect.has_key(hint):
            del self.expect[hint]

    def do_button_press_event(self, event):
        Vte.Terminal.do_button_press_event(self, event)

        # 鼠标右键按下
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            if self.get_has_selection():
                self.copy_clipboard()
                self.unselect_all()
            else:
                self.paste_clipboard()

    def do_contents_changed(self):
        text = self.get_text()[0].strip()
        if text == self.last_text:
            return
        self.last_text = text

        # expect
        for k,e in self.expect.items():
            if text.endswith(k):
                self.feed_child(e.val + "\n", -1)
                if e.once:
                    if e.checkMenuItem != None:
                        e.checkMenuItem.set_active(False)
                    else:
                        del self.expect[k]
                return

    def do_window_title_changed(self):
        if self.call_title_changed != None:
            self.call_title_changed(self.get_window_title())
