# -*- coding:utf8 -*-

#禁用 menu proxy for ubuntu
import os
os.environ["UBUNTU_MENUPROXY"] = "0"

from expect import Expect
from frame import Frame, AbsTab, TabHead
from term import Term
