#-*- encoding:utf-8 -*-
"""Generic linux daemon base class for python 3.x.""" 

import sys
import os
import time
import atexit
import signal

from logging import getLogger

PKG = "daemon" 
logger = getLogger(PKG)

class daemon:
    """A generic daemon class.

    Usage: subclass the daemon class and override the run() method.""" 

    def __init__(self, pidfile):
        self.pidfile = pidfile

    def daemonize(self):
        """Deamonize class. UNIX double fork mechanism."""    #<-- double fork 이유는 session leader 가 되지 않기위함.
                                #    session leader 는 tty 의 제어권을 가지게됨.
        try:
            pid = os.fork()                    #<-- 1. 첫번째 fork

            if pid > 0:
                # exit first parent
                logger.info("Main Process ends.")
                sys.exit(0)                    #<-- 2. 부모 프로세스는 종료.
        except OSError as err:
            logger.error("fork #1 failed: {}, exited:1\n".format(err))
            sys.exit(1)

        # decouple from parent environment
        logger.debug("Decouple from parent environment.")    #<-- 3. 자식 프로세스는 부모의 환경으로부터 decouple 함.
        os.chdir('/')                        #<-- 4. 현재 디렉토리 위치를 root 로 이동.
        os.setsid()                        #<-- 5. 자식 프로세스가 process group leader 가 아니라면 새로운 세션의 leader 가 되도록 하는 명령.
        os.umask(0)                        #<-- 6. 초기 파일, 디렉토리 권한을 그대로 사용하겠다는 뜻.

        # do second fork
        logger.debug("Do second fork.")
        try:
            pid = os.fork()                    #<-- 7. 5에서 부모는 session leader 이고 자식은 session leader 가 아니게되면서 tty 제어권 상실 목적
            if pid > 0:
                logger.info("fork #1 normally exited.")
                sys.exit(0)                    #<-- 8. 두번째 부모 프로세스 종료
        except OSError as err:
            logger.error('fork #2 failed: {}, exited:1\n'.format(err))
            sys.exit(1)

        # redirect standard file descriptors
        logger.debug("Redirect standard file descriptors.")
        sys.stdout.flush()                    #<-- 9. standard out 버퍼 flush
        sys.stderr.flush()                    #<-- 10. standard error 버퍼 flush
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())        #<-- 11. standard in, out, error 를 /dev/null로 redirect
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        try:
            with open(self.pidfile,'w+') as f:
                f.write(pid + '\n')
        except BaseException as e:
            logger.error("Writing the pid file error:{}".format(e))

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """Start the daemon.""" 

        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile,'r') as pf:

                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if pid:
            message = "pidfile {0} already exist. " + \
                    "Daemon already running?\n" 
            sys.stderr.write(message.format(self.pidfile))
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        logger.info("Daemonize Done")
        self.run()

    def stop(self):
        """Stop the daemon.""" 

        # Get the pid from the pidfile
        try:
            with open(self.pidfile,'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if not pid:
            message = "pidfile {0} does not exist. " + \
                    "Daemon not running?\n" 
            sys.stderr.write(message.format(self.pidfile))
            return # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            e = str(err.args)
            if e.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print (str(err.args))
                sys.exit(1)

    def restart(self):
        """Restart the daemon.""" 
        self.stop()
        self.start()

    def run(self):
        """You should override this method when you subclass Daemon.

        It will be called after the process has been daemonized by
        start() or restart().""" 
        self._run()
