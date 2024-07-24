# Copyright © 2008-2022 Jakub Wilk <jwilk@jwilk.net>
# Copyright © 2022-2024 FriedrichFroebel
#
# This file is part of ocrodjvu.
#
# ocrodjvu is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# ocrodjvu is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.

"""
Interprocess communication.
"""

import errno
import logging
import os
import re
import shlex
import signal
import subprocess


# CalledProcessError, CalledProcessInterrupted
# ============================================

# Protect from scanadf[0] and possibly other software that sets SIGCHLD to SIG_IGN.
# [0] https://bugs.debian.org/596232
if os.name == 'posix':
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)


def get_signal_names():
    signame_pattern = re.compile('^SIG[A-Z0-9]*$')
    data = dict(
        (name, getattr(signal, name))
        for name in dir(signal)
        if signame_pattern.match(name)
    )
    try:
        if data['SIGABRT'] == data['SIGIOT']:
            del data['SIGIOT']
    except KeyError:  # no coverage
        pass
    try:
        if data['SIGCHLD'] == data['SIGCLD']:
            del data['SIGCLD']
    except KeyError:  # no coverage
        pass
    return dict((no, name) for name, no in data.items())


CalledProcessError = subprocess.CalledProcessError


class CalledProcessInterrupted(CalledProcessError):
    _signal_names = get_signal_names()

    def __init__(self, signal_id, command):
        Exception.__init__(self, command, signal_id)
        self.by_user = signal_id == signal.SIGINT

    def __str__(self):
        signal_name = self._signal_names.get(self.args[1], self.args[1])
        return f'Command {self.args[0]!r} was interrupted by signal {signal_name}'


del get_signal_names


# Subprocess
# ==========

class Subprocess(subprocess.Popen):

    @classmethod
    def override_env(cls, override):
        env = os.environ
        # We would like to:
        # - preserve LC_CTYPE (which is required by some DjVuLibre tools),
        # - but reset all other locale settings (which tend to break things).
        lc_ctype = env.get('LC_ALL') or env.get('LC_CTYPE') or env.get('LANG')
        env = {
            k: v
            for k, v in env.items()
            if not (k.startswith('LC_') or k in ('LANG', 'LANGUAGE'))
        }
        if lc_ctype:
            env['LC_CTYPE'] = lc_ctype
        if override:
            env.update(override)
        return env

    def __init__(self, *args, **kwargs):
        kwargs['env'] = self.override_env(kwargs.get('env'))
        if os.name == 'posix':
            kwargs.update(close_fds=True)
        try:
            commandline = kwargs['args']
        except KeyError:
            commandline = args[0]
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(str.join(' ', map(shlex.quote, commandline)))
        self.__command = commandline[0]
        self.__wait_called = False
        try:
            subprocess.Popen.__init__(self, *args, **kwargs)
        except EnvironmentError as ex:
            suffix = ': ' + repr(self.__command)
            if ex.strerror.endswith(suffix):
                # https://bugs.python.org/issue32490
                ex.strerror = ex.strerror[:-len(suffix)]
            ex.filename = self.__command
            raise

    def wait(self, *args, **kwargs):
        return_code = subprocess.Popen.wait(self, *args, **kwargs)
        self.__wait_called = True
        if return_code > 0:
            raise CalledProcessError(return_code, self.__command)
        if return_code < 0:
            raise CalledProcessInterrupted(-return_code, self.__command)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Calling `self.wait` twice will always result in a return code > 0.
        # For this reason, use a patched `__exit__` method if we already have called `self.wait` before.
        # The original `subprocess.Popen.__exit__` method will always call `self.wait` at the end.
        # In the best case, we would not need this special handling, but this would require us to further
        # rewrite the code for the Tesseract and Cuneiform engine.
        if self.__wait_called:
            self._exit_without_wait(exc_type, exc_val, exc_tb)
            return
        subprocess.Popen.__exit__(self, exc_type, exc_val, exc_tb)

    def _exit_without_wait(self, exc_type, exc_val, exc_tb):
        # Copy of `subprocess.Popen.__exit__`, but with `wait` removed as this will call the above `wait`
        # method and lead to a return code > 0.
        if self.stdout:
            self.stdout.close()
        if self.stderr:
            self.stderr.close()
        try:  # Flushing a BufferedWriter may raise an error
            if self.stdin:
                self.stdin.close()
        finally:
            pass


# PIPE
# ====

PIPE = subprocess.PIPE

# DEVNULL
# =======

try:
    DEVNULL = subprocess.DEVNULL
except AttributeError:
    DEVNULL = open(os.devnull, 'rw')


# require()
# =========

def require(command):
    directories = os.environ['PATH'].split(os.pathsep)
    for directory in directories:
        path = os.path.join(directory, command)
        if os.access(path, os.X_OK):
            return
    raise OSError(errno.ENOENT, 'command not found', command)


# logging support
# ===============

logger = logging.getLogger('ocrodjvu.ipc')


# __all__
# =======

__all__ = [
    'CalledProcessError', 'CalledProcessInterrupted',
    'Subprocess', 'PIPE', 'DEVNULL',
    'require',
]
