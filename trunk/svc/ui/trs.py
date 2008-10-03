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

from svc.egg import PythonEgg
from xml.dom.minidom import parse as ParseDOM
import re
import codecs

# Text format:
#
# zakaznik: /11.81 dobry den [Vodafone] {vodafoun} <ehm_ANO>
# |speaker| |sync| |----transcript----| |-comment| |-event-|

class Transcript(PythonEgg):
    def __init__(self, dom):
        super(Transcript, self).__init__()
        self._dom = dom
        self._updateTurns()
        self._updateSpeakers()

    def _updateTurns(self):
        self._turns = self._dom.getElementsByTagName('Turn')

    def _updateSpeakers(self):
        self._speakers = {'': 'N/A'}
        for node in self._dom.getElementsByTagName('Speaker'):
            id = node.getAttribute('id')
            name = node.getAttribute('name')
            self._speakers[id] = name

        self._speakersReverse = dict((v, k) for (k, v) in self._speakers.iteritems())

    def __iter__(self):
        for i in self._turns:
            yield self._DOMToText(i)

    def __getitem__(self, i):
        turn = self._turns[i]
        return self._DOMToText(turn)

    def __len__(self):
        return len(self._turns)

    def _DOMToText(self, node):
        ret = []
        for child in node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                words = child.data.split()
                ret.extend(words)
            elif child.nodeType == child.ELEMENT_NODE:
                meth_name = '_%s_DOMToText' % child.tagName
                conv = getattr(self, meth_name, None)
                if conv is not None:
                    ret.append(conv(child))
        text = ' '.join(ret)

        spkrs_id = node.getAttribute('speaker').split()
        spkr = ' '.join(self._speakers.get(i, 'unknown') for i in spkrs_id)

        return '%s:\t%s' % (spkr, text)

    def _Event_DOMToText(self, node):
        extent = node.getAttribute('extent')
        desc = node.getAttribute('desc')
        tmpl = '<UNKNOWN:%s>'
        if extent == 'instantaneous':
            tmpl = '<%s>'
        elif extent == 'begin':
            tmpl = '<%s_|>'
        elif extent == 'end':
            tmpl = '<|_%s>'
        elif extent == 'previous':
            tmpl = '<<_%s>'
        elif extent == 'next':
            tmpl = '<%s_>>'
        return tmpl%desc

    def _Event_TextToDOM(self, text, dom):
        node = dom.createElement('Event')
        if text.endswith('_|'):
            extent = 'begin'
            desc = text[:-2]
        elif text.startswith('|_'):
            extent = 'end'
            desc = text[2:]
        elif text.endswith('_>'):
            extent = 'next'
            desc = text[:-2]
        elif text.startswith('<_'):
            extent = 'previous'
            desc = text[2:]
        else:
            extent = 'instantaneous'
            desc = text
        node.setAttribute('extent', extent)
        node.setAttribute('desc', desc)
        return node

    def _Comment_DOMToText(self, node):
        desc = node.getAttribute('desc')
        tmpl = '{%s}'
        return tmpl%desc
    
    def _Comment_TextToDOM(self, text, dom):
        node = dom.createElement('Comment')
        node.setAttribute('desc', text)
        return node

    def _Sync_DOMToText(self, node):
        time = node.getAttribute('time')
        tmpl = '/%s'
        return tmpl%time

    def _Sync_TextToDOM(self, text, dom):
        node = dom.createElement('Sync')
        node.setAttribute('time', text)
        return node

    def _newline(self):
        return self._dom.createTextNode('\n')

    def __setitem__(self, i, text):
        node = self._turns[i]
        self._TextToDOM(text, self._dom, node)

    def _cleanDOMNode(self, node):
        while node.firstChild is not None:
            child = node.firstChild
            node.removeChild(child)
            child.unlink()

    def _TextToDOM(self, text, dom, into):
        RE_PARSE = re.compile(r'((?P<spkr>^.*?):\s*|<(?P<Event>([^>]*_>|[^>]*))>|{(?P<Comment>[^}]*)}|/(?P<Sync>[\d.]*)\s*)|(?P<text>[^/{<]+)')

        self._cleanDOMNode(into)

        syncs = []

        into.appendChild(self._newline())

        for match in RE_PARSE.finditer(text):
            for element, value in match.groupdict().iteritems():
                if value is not None:
                    if element == 'spkr':
                        #TODO: NEEDS to fix to handle more speakers
                        if value not in self._speakersReverse:
                            self.createNewSpeaker(value)
                        spkr_id = self._speakersReverse[value]
                        into.setAttribute('speaker', spkr_id)
                        node = None

                    elif element == 'text':
                        node = dom.createTextNode(value)
                    else:
                        meth_name = '_%s_TextToDOM' % element
                        conv = getattr(self, meth_name, None)
                        if conv is not None:
                            node = conv(value, dom)
                        else:
                            node = None

                    if element == 'Sync':
                        syncs.append(value)
                    elif element != 'spkr':
                        syncs.append(None)

                    if node is not None:
                        into.appendChild(node)
                        into.appendChild(self._newline())

    @classmethod
    def loadFromFile(cls, fn):
        dom = ParseDOM(fn)
        return cls(dom)

    def writeToFile(self, fn):
        fw = codecs.open(fn, 'w', 'utf-8')
        try:
            self._dom.writexml(fw, addindent='', newl='', encoding='utf-8')
        finally:
            fw.close()

    def createNewSpeaker(self, name, type='unknown'):
        if type not in ['unknown', 'male', 'female']:
            raise ValueError("Unknown speaker type: %s" % type)

        id_no = 1
        while True:
            spkr_id = 'spk%d' % id_no
            if spkr_id not in self._speakers:
                break
            id_no += 1

        section = self._dom.getElementsByTagName('Speakers')[0]

        node = self._dom.createElement('Speaker')
        node.setAttribute('accent', '')
        node.setAttribute('check', 'no')
        node.setAttribute('dialect', 'native')
        node.setAttribute('id', spkr_id)
        node.setAttribute('name', name)
        node.setAttribute('scope', 'local')
        node.setAttribute('type', type)

        section.appendChild(node)
        section.appendChild(self._newline)
        
        self._updateSpeakers()


