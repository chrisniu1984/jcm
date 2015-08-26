# -*- coding:utf-8 -*-

class Expect:
    def __init__(self, hint, val, once=False, checkMenuItem=None):
        self.hint = hint
        self.val = val
        self.once = once
        self.checkMenuItem = checkMenuItem
    
    @staticmethod
    def new_from_dict(d, checkMenuItem=None):
        if not d.has_key("hint") or not d.has_key("val"):
            return None
        hint = d["hint"]
        val = d["val"]
    
        once = False
        if d.has_key("once") and d["once"] == "true":
            once = True
    
        return Expect(hint=hint, val=val, once=once, checkMenuItem=checkMenuItem)
