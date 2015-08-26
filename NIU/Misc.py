# -*- coding:utf8 -*-

import os
import sys

def execute(cmd, cwd=""):
    argv = tuple(cmd.split(" "))

    if len(cwd) == 0:
        cwd = os.getcwd()

    pid = os.fork()

    # 子进程
    if pid == 0:
        # 孙子进程运行app
        if os.fork() == 0:
            env = os.environ
            env["PWD"] = cwd
            os.execvpe(argv[0], argv, env)
        # 子进程退出，让孙子进程被init领养
        else:
            sys.exit(0)

    # 父进程等一下子进程
    elif pid > 0:
        os.waitpid(pid, 0)
    else:
        print "fork error"
