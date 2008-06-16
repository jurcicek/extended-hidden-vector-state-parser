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

import re
from string import Template

class ExTemplate(Template):
    places = {
        'exact': r'^%s$',
        'space': r'^\s*%s\s*$',
        'space_start': r'^\s*%s$',
        'space_end': r'^%s\s*$',
        'ignore': r'^.*%s.*$',
        'ignore_start': r'^.*%s$',
        'ignore_end': r'^%s.*$',
    }
    def __init__(self, template, placing='exact'):
        super(Template, self).__init__(template)
        self._makeBlPattern(template, placing)

    def _makeBlPattern(self, template, placing):
        tesc = ''
        from_ = 0
        for match in self.pattern.finditer(template):
            start, end = match.span()
            tesc += re.escape(template[from_:start])
            tesc += template[start:end]
            from_ = end
        else:
            tesc += re.escape(template[from_:])
        try:
            place = self.places[placing]
        except KeyError:
            raise ValueError("Unknown placing: %r" % placing)

        def bl_replace(match):
            d = match.groupdict()
            named = d['named']
            braced = d['braced']
            escaped = d['escaped']
            invalid = d['invalid']
            if named is not None:
                ret = r'(?P<%s>.*)' % named
            elif braced is not None:
                ret = r'(?P<%s>.*)' % braced
            elif invalid is not None:
                raise ValueError("Invalid reference")
            else:
                ret = re.escape(escaped)
            return ret

        blpat = place % self.pattern.sub(bl_replace, tesc)
        self.blpattern = re.compile(blpat)

    def backload(self, s):
        match = self.blpattern.search(s)
        if match is None:
            return None
        else:
            return match.groupdict()
