# SVC library - usefull Python routines and classes
# Copyright (C) 2006-2008 Jan Svec, honza.svec@gmail.com
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

def fsplit(path):
    """Recursive call of `os.path.split`

    It splits `path` by recursive calling of `os.path.split` and returns lists
    of path elements.

    :RType: list
    """
    ret = []
    while path not in ['', '/']:
        path, last = os.path.split(path)
        ret.insert(0, last)
    if path:
        ret.insert(0, path)
    return ret

def fjoin(path):
    """Recursive call of `os.path.join`

    It joins path elements given by list `path` into single string using
    `os.path.join`.

    :RType: str
    """
    ret = path[0]
    for i in range(1, len(path)):
        ret = os.path.join(ret, path[i])
    return ret

def mkdirp(path):
    """Make directory `path` possibly creating its parents

    If some of parent paths exists, nothing will happen. But if this path is
    not a directory, OSError will be raised.
    """
    path = fsplit(path)
    full = ''
    for elm in path:
        full = os.path.join(full, elm)
        if os.path.exists(full):
            if not os.path.isdir(full):
                raise OSError("Path %r is not directory" % full)
        else:
            os.mkdir(full)


