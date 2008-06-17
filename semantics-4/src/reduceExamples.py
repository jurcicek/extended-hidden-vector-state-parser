#!/usr/bin/env python2.4
from svc.scripting import *
from svc.utils import ADict
from svc.map import SymMap

class ReduceExamples(Script):
    options = {
        'concept_map': (Required, String),
        'sym_map': (Required, String),
        'examples': (Required, String),
        'output': (Required, String),
    }

    posOpts = ['concept_map', 'sym_map', 'examples', 'output']

    def mapExamples(self, dict):
        ret = ADict()
        for concept_word, count in dict.iteritems():
            if len(concept_word) != 2:
                # TODO: REMOVE: used only with bigram_lemma
                continue
            c, w = concept_word
            if c not in self.conceptMap:
                continue
            if w not in self.symMap:
                continue
            ret[c, w] += count
        return ret

    def main(self, concept_map, sym_map, examples, output):
        self.conceptMap = SymMap.readFromFile(concept_map, format=(int, unicode)).inverse
        self.symMap = SymMap.readFromFile(sym_map, format=(int, unicode)).inverse

        examples = ADict.readFromFile(examples)
        examples = self.mapExamples(examples)
        examples.writeToFile(output)

if __name__ == '__main__':
    s = ReduceExamples()
    s.run()
