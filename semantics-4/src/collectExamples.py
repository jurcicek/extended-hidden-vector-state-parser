#!/usr/bin/env python2.4
from svc.scripting import *
from svc.utils import ADict
from svc.ui.dxml import DXML
from svc.ui.treedist import OrderedTree

from glob import glob
from math import log
import codecs
from svc.ui.smntcs import input
import sys

DEPENDENT_CONCEPTS = [
    ['AMOUNT', 'LENGTH', 'NUMBER'],
    ['STATION'],
    ['TRAIN_TYPE'],
]

DOMINATED_CONCEPTS = set(['ACCEPT', 'ARRIVAL', 'DELAY', 'DEPARTURE',
    'DISTANCE', 'DURATION', 'PLATFORM', 'PRICE', 'REJECT'])


CONCEPT_GROUPING = {
    'AMOUNT': ['LENGTH', 'NUMBER', 'TIME'],
    'LENGTH': ['NUMBER', 'AMOUNT', 'TIME'],
    'NUMBER': ['LENGTH', 'AMOUNT', 'TIME'],
}

NUMBER_CONCEPTS = set(['AMOUNT', 'LENGTH', 'NUMBER', 'TIME'])


class CollectExamples(Script):
    options = {
        'files': (Required, Multiple, String),
        'posout': String,
        'negout': String,
        'pos_method': String,
        'neg_method': String,
        'disable_ne': Flag,
        'disable_common': Flag,
        'dataset': (Required, String),
        'default_datasets': (Required, String),
    }

    posOpts = ['files', Ellipsis]

    def globFiles(self, files, mask):
        globfiles = set()
        for fn in files:
            if os.path.isdir(fn):
                globfiles |= set(glob(os.path.join(fn, mask)))
            else:
                globfiles.add(fn)

        return sorted(globfiles)

    def filterNEtext(self, da):
        ret = []
        for item in da:
            if self.disable_ne:
                ne_type = None
            else:
                ne_type = item[0]
            text = [i.lower() for i in item[1:]]

            if ne_type is not None:
                ne_type = ne_type.upper()
            if ret and ret[-1][0] == ne_type:
                ret[-1][1].append(text)
            else:
                ret.append((ne_type, [text]))
        return ret

    def generalizer(self, parent, common_dataset):
        for da in parent:
            da['generalized'] = da[common_dataset]
            for lemma, pos in zip(da[common_dataset], da['pos']):
                self.posTags[lemma].add(pos)

            # da['generalized'] = generalized = []
            # for lemma, pos in zip(da['lemma'], da['pos']):
            #     g = lemma
            #     for mask in ['Cn', 'Cl', 'Cr', 'Ch']:
            #         if pos.startswith(mask):
            #             g = mask
            #             break
            #     generalized.append(g)
            yield da

    def genNETypeWordConcept(self, files, datasets, common_dataset, default_dataset):
        g = input.MultiReader(files, input.DXMLReader)
        g = input.InputGenerator(g, datasets, default_dataset)
        g = self.generalizer(g, common_dataset)
        for da in g:
            type_counts = ADict()

            ne_typed = [(ne_type,)+(g,)+w for ne_type, g, w in 
                            zip(da['ne_typed'], da['generalized'], da['requested'])]

            filtered = self.filterNEtext(ne_typed)

            for item in filtered:
                ne_type = item[0]
                if ne_type is not None:
                    type_counts[ne_type.upper()] += 1

            semantics = da.get('semantics', '')
            tree = OrderedTree.fromString(semantics)
            tree_counts = tree.getConceptCounts()
            bad_ne = set()
            for concept, count in type_counts.iteritems():
                if tree_counts.get(concept, 0) != count:
                    bad_ne.add(concept)

            ne_types = set(type_counts.keys()) - set(bad_ne)

            if not bad_ne:
                splits = tree.splitStateVector(*list(ne_types))
                for (ne_type, text), states in zip(filtered, splits):
                    yield ne_type, text, states
            else:
                # Some conflicts or no named entities
                states = tree.toStateVector()
                for (ne_type, text) in filtered:
                    if ne_type in tree.conceptCounts:
                        only_states = [i for i in states if ne_type in i]
                        yield ne_type, text, only_states
                    else:
                        yield ne_type, text, states

    def otherConceptsFromGroup(self, c):
        ret = set(CONCEPT_GROUPING.get(c, []))
        ret.add(c)
        return ret

    def collectPos_basic(self, stacks, words):
        pos_ex = ADict()
        for stack in stacks:
            c = stack[-1]
            if c is None:
                # Ignore superroot of tree
                continue
            for c_ in self.otherConceptsFromGroup(c):
                for w in words:
                    pos_ex[c_, w] += 1
        return pos_ex

    def collectPos_netyped(self, ne_type, words):
        pos_ex = ADict()
        if ne_type is not None:
            for w in words:
                pos_ex[ne_type, w] += 1
        return pos_ex

    def collectNeg_basic(self, stacks, words):
        neg_ex = ADict()

        concepts = set()
        for stack in stacks:
            concepts |= set(stack)
        for rootConcept in DOMINATED_CONCEPTS:
            if rootConcept in concepts:
                # the utterance can be used as negative example 
                
                for leafConcepts in DEPENDENT_CONCEPTS:
                    # you have one group of dependent concepts (generally numbers)
                    ok = True
                    for leafConcept in leafConcepts:
                        if leafConcept in concepts:
                            ok = False
                    
                    if ok:
                        # all words in the utterance can be used as negative
                        # exapmles beceause they are not connected with
                        # lexConceptsDependent (the example does not contain
                        # lexConceptsDependent)
                        
                        for leafConcept in leafConcepts:
                            for w in words:
                                neg_ex[leafConcept, w] += 1

                # the example was already used
                break

        return neg_ex

    def collectNeg_derived(self, histories, words, pos_ex):
        neg_ex = ADict()
        concepts = set()
        for stack in histories:
            concepts.add(stack[-1])

        for c in concepts:
            for w in words:
                if pos_ex[c, w] == 0:
                    neg_ex[c, w] += 1
        return neg_ex

    def collectNeg_derclass(self, histories, words, pos_ex):
        neg_ex = ADict()
        concepts = set()

        for conceptGroup in DEPENDENT_CONCEPTS:
            concepts |= set(conceptGroup)

        for c in concepts:
            for w in words:
                if pos_ex[c, w] == 0:
                    neg_ex[c, w] += 1
        return neg_ex

    def collectExamples(self, files, dataset, common_dataset, default_dataset, pos_method, neg_method):
        pos_ex = ADict()
        neg_ex = ADict()
        netyped_ex = ADict()

        equiv = ADict(default=set)

        all_stacks = set()
        all_words = set()

        for ne_type, fw, stacks in self.genNETypeWordConcept(files, [dataset], common_dataset, default_dataset):
            items = zip(*fw)
            words = items[0]
            for w, word in fw:
                all_words.add(w)
                equiv[w].add(word)

            for stack in stacks:
                stack = stack[1:]  # Skip superroot None
                if stack:
                    all_stacks.add(tuple(stack))


            # Collection of positive examples
            if pos_method in ('basic', 'netyped'):
                pos_ex += self.collectPos_basic(stacks, words)
            
            if pos_method == 'netyped':
                netyped_ex += self.collectPos_netyped(ne_type, words)

            # Collection of negative examples
            if neg_method == 'basic':
                neg_ex += self.collectNeg_basic(stacks, words)

        if neg_method == 'derived':
            neg_ex += self.collectNeg_derived(all_stacks, all_words, pos_ex)
        elif neg_method == 'derclass':
            neg_ex += self.collectNeg_derclass(all_stacks, all_words, pos_ex)

        if pos_method == 'netyped':
            pos_ex = netyped_ex

        return pos_ex, neg_ex, equiv

    def lemmaWasNumber(self, lemma):
        for pos in self.posTags[lemma]:
            if pos.startswith('C'):
                return True
        return False

    def filterNumberNegEx(self, ex):
        ret = {}
        for (concept, common), count in ex.iteritems():
            if concept in NUMBER_CONCEPTS and self.lemmaWasNumber(common):
                pass
            else:
                ret[concept, common] = count
        return ret

    def doEquivalenceTable(self, ex, table):
        ret = ADict()
        for (concept, common), count in ex.iteritems():
            for w in table[common]:
                ret[concept, w] = count
        return ret

    def main(self, files, dataset, default_datasets, posout=None, negout=None, pos_method='basic',
            neg_method='basic', disable_ne=False, disable_common=False):

        if pos_method not in ['basic', 'netyped', 'off']:
            raise ValueError("Unsupported pos_method: %s" % pos_method)

        if neg_method not in ['basic', 'derived', 'derclass', 'off']:
            raise ValueError("Unsupported neg_method: %s" % neg_method)

        default_dataset, common_dataset = default_datasets.split(',')

        if disable_common:
            common_dataset = dataset

        self.disable_ne = disable_ne
        files = self.globFiles(files, '*.xml')

        self.posTags = ADict(default=set)

        if dataset == 'off':
            pos_ex = ADict()
            neg_ex = ADict()
            equiv = ADict()
        else:
            pos_ex, neg_ex, equiv = self.collectExamples(files, dataset, common_dataset, default_dataset, pos_method, neg_method)

        neg_ex = self.filterNumberNegEx(neg_ex)

        pos_ex = self.doEquivalenceTable(pos_ex, equiv)
        neg_ex = self.doEquivalenceTable(neg_ex, equiv)

        key=lambda (k,v): (k[0], -v, k[1])

        if posout is not None:
            pos_ex.writeToFile(posout, key=key, format='%r')
        if negout is not None:
            neg_ex.writeToFile(negout, key=key)


if __name__ == '__main__':
    s = CollectExamples()
    s.run()
