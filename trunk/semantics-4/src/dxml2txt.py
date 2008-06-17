#!/usr/bin/env python2.4

from svc.scripting import *
import sys
import codecs
from xml.dom.minidom import parse

class DXML2TXT(Script):
    options = {
        'infile': String,
        'outfile': String,
    }

    def transformFile(self, fr, fw):
        dom = parse(fr)
        for element in dom.getElementsByTagName("text"):
            if element.getAttribute('type') == 'normalized':
                ret = []
                for node in element.childNodes:
                    if node.nodeType == node.TEXT_NODE:
                        ret.append(node.data.strip())
                print >> fw, ' '.join(ret)
        
    def main(self, infile=None, outfile=None):
        if infile == '-':
            infile = None
        if outfile == '-':
            outfile = None

        if infile is None:
            infile = sys.stdin
        else:
            infile = file(infile, 'r')

        if outfile is None:
            outfile = codecs.getwriter('utf-8')(sys.stdout)
        else:
            outfile = codecs.open(outfile, 'w', 'utf-8')

        self.transformFile(infile, outfile)
        infile.close()
        outfile.close()

if __name__ == '__main__':
    s = DXML2TXT()
    s.run()
