import xml.dom.minidom 
import codecs
import re

from svc.egg import PythonEgg

class DXML(PythonEgg):
    def __init__(self, domDocument):
        super(DXML, self).__init__()
        self._dom = domDocument

    @classmethod
    def readFromFile(cls, fn):
        dom = xml.dom.minidom.parse(fn) 
        inst = cls(dom)
        return inst

    def writeToFile(self, fn):
        self._dom.normalize()
        self._cleanTextNodes()
        fw = codecs.open(fn, 'w', 'utf-8')
        try:
            self._dom.writexml(fw, addindent='  ', newl='\n', encoding='utf-8')
        finally:
            fw.close()

    def _getNodeText(self, node):
        s = []
        for child in node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                s.append(child.data)
        s = ' '.join(s)
        s = re.sub(r'\[[^\]]*\]', '', s)
        s = re.sub(r' +', ' ', s)
        s = s.strip()
        return s

    def _getNodeAttributes(self, node, skip=[]):
        ret = {}
        for name, attr in node.attributes.items():
            if name in skip:
                continue
            ret[name] = attr
        return ret

    def _setNodeAttributes(self, node, attrs):
        for name, value in attrs.items():
            node.attributes[name] = value

    def _cleanTextNodes(self, node=None):
        if node is None:
            node = self._dom
        child = node.firstChild
        while child is not None:
            if child.nodeType == child.TEXT_NODE:
                child_new = child.nextSibling
                child.parentNode.removeChild(child)
                child = child_new
                continue
            if child.nodeName not in ['text', 'dialogue_act', 'parametrized_act']:
                self._cleanTextNodes(child)
            else:
                self._stripTextNode(child)
            child = child.nextSibling

    def _stripTextNode(self, node):
        txt = node.firstChild
        if txt is None:
            return
        if node.firstChild.nodeType != node.firstChild.TEXT_NODE or len(node.childNodes) != 1:
            raise ValueError("Bad tag: <%s>" % node.nodeName)
        txt.data = txt.data.strip()

    def getUtterances(self):
        ret = []
        for utterance in self._dom.getElementsByTagName('utterance'):
            ret.append(self._getNodeAttributes(utterance))
        return ret

    def getDialogueTypes(self):
        ret = set(['normalized'])
        for da in self._dom.getElementsByTagName('parametrized_act'):
            type = da.getAttribute('type')
            if type:
                ret.add(type)
        return ret

    def getDialogueActs(self, type='normalized'):
        if type == 'normalized':
            tagName = 'dialogue_act'
            type = ''
        else:
            tagName = 'parametrized_act'
        ret = []
        for utterance in self._dom.getElementsByTagName('utterance'):
            ut = []
            for da in utterance.getElementsByTagName(tagName):
                if da.getAttribute('type') == type:
                    s = self._getNodeText(da)
                    ut.append((s, self._getNodeAttributes(da, ['type'])))
            ret.append(ut)
        return ret

    def getSemantics(self, type='normalized'):
        ret = []
        for utter in self.getDialogueActs(type):
            ut = []
            for text, attrs in utter:
                ut.append(attrs['semantics'])
            ret.append(ut)
        return ret

    def getTexts(self, type='normalized'):
        ret = []
        for utterance in self._dom.getElementsByTagName('utterance'):
            ut = None
            for txt in utterance.getElementsByTagName('text'):
                if txt.getAttribute('type') == type:
                    s = self._getNodeText(txt)
                    if ut is not None:
                        raise ValueError("Multiple <text> tags with the same type per one utterance")
                    ut = (s, self._getNodeAttributes(txt, ['type']))
            ret.append(ut)
        return ret

    def removeDialogueActs(self, type='normalized'):
        if type == 'normalized':
            tagName = 'dialogue_act'
            type = ''
        else:
            tagName = 'parametrized_act'
        for da in self._dom.getElementsByTagName(tagName):
            if da.getAttribute('type') == type:
                da.parentNode.removeChild(da)

    def removeTexts(self, type):
        for txt in self._dom.getElementsByTagName('text'):
            if txt.getAttribute('type') == type:
                txt.parentNode.removeChild(txt)

    def setDialogueActs(self, type, acts):
        if type == 'normalized':
            tagName = 'dialogue_act'
            type = None
        else:
            tagName = 'parametrized_act'
        for utterance, new_utter in zip(self._dom.getElementsByTagName('utterance'), acts):
            for txt, attrs in new_utter:
                new_tag = self._dom.createElement(tagName)
                new_txt = self._dom.createTextNode(txt)
                utterance.appendChild(new_tag)
                new_tag.appendChild(new_txt)
                self._setNodeAttributes(new_tag, attrs)
                if type is not None:
                    new_tag.attributes['type'] = type

    def setTexts(self, type, texts):
        for utterance, (txt, attrs) in zip(self._dom.getElementsByTagName('utterance'), texts):
            new_tag = self._dom.createElement('text')
            new_txt = self._dom.createTextNode(txt)
            utterance.appendChild(new_tag)
            new_tag.appendChild(new_txt)
            self._setNodeAttributes(new_tag, attrs)
            new_tag.attributes['type'] = type

    def unlink(self):
        self._dom.unlink()
