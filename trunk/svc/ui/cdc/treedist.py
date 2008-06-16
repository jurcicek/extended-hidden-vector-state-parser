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

import sys
import os
import time
from itertools import izip

from svc.scripting import *
from svc.utils import issequence, ADict, cartezian
from svc.ui.treedist import OrderedTree, TreeDist, CommonDist, EditScript

ROOT_CONCEPT = '__S'

CONCEPT_GROUPS = {
    'DA': ['ACKNOWLEDGEMENT', 'CLOSING', 'DISCONNECT', 'OPENING', 'OTHER',
           'PRESENT_INFO', 'REQUEST_INFO', 'THANKING',],
    'SKIP': ['_DUMMY_', '_FILLER_'],
}

def utils_dict_sum(*dicts):
    ret = {}
    for d in dicts:
        for key, value in d.iteritems():
            ret[key] = ret.get(key, 0) + value
    return ret

class ConceptTree(OrderedTree):
    def getConceptCount(self):
        count = 1
        for child in self:
            if hasattr(child, 'getConceptCount'):
                count += child.getConceptCount()
            else:
                count += 1
        return count

    def __str__(self):
        ret = super(ConceptTree, self).__str__()
        if self.label == ROOT_CONCEPT:
            ret = ret[4:-1]
        return ret

class ConceptLine(list):
    def __init__(self, separator, only=None, skip=None):
        super(ConceptLine, self).__init__()
        self._separator = separator
        self._only = only
        self._skip = skip

    def addSeparator(self):
        self.append(self._separator)

    def removeSeparator(self):
        while self and self[-1] == self._separator:
            del self[-1]

    def flushLine(self):
        self.removeSeparator()
        ret = ''.join(self)
        del self[:]
        try:
            ret = ConceptTree.fromString(ret, label=ROOT_CONCEPT)
            if self._only:
                ret.removeNodesWithoutLabels(self._only)
            if self._skip:
                ret.removeNodesWithLabels(self._skip)
            return ret
        except ValueError:
            return None

class TreeDistScript(ExScript):
    """Tools for compute tree-edit-distance on input Files.
    """
    options = {
        'command': ExScript.CommandParam,
        'signif.files': (Required, Multiple, String),
        'signif.bucktype': String,
        'mlf2sgml.files': OptionAlias,
        'mlf2sgml.bucktype': OptionAlias,
        'editscripts.files': OptionAlias,
        'kappa.files': OptionAlias,
        'kappa.nconc': Integer,
        'matching.files': OptionAlias,
        'sresults.files': OptionAlias,
        'sresults.only': (Multiple, String),
        'sresults.skip': (Multiple, String),
        'sresults.twoside': Flag,
        'sresults.groupby': String,
    }

    posOpts = ['command', 'files', Ellipsis]

    debugMain = True

    def createConceptGroups(self, grp):
        if not issequence(grp):
            grp = [grp]
        ret = []
        for item in grp:
            for i in item.split(','):
                if i.startswith('@'):
                    ret.extend(CONCEPT_GROUPS.get(i[1:], []))
                else:
                    ret.append(i)
        return set(ret)

    def readForestFromMLF(self, in_fn, only=None, skip=None):
        SEPARATOR = ', '
        OPEN_PAR = '('
        CLOSING_PAR = ')'
        HEADER = '#!MLF!#'

        if only is not None:
            only = self.createConceptGroups(only)
        if skip is not None:
            skip = self.createConceptGroups(skip)

        fr = file(in_fn)
        forest = {}
        try:
            header = fr.readline().strip()
            if header != HEADER:
                self.logger.error("Not a MLF file: %r", in_fn)
                return
            filename_line = True
            concept_line = ConceptLine(SEPARATOR, only, skip)
            for line in fr:
                line = line.strip()
                if not line:
                    continue
                if line[0] == '#':
                    continue
                if filename_line:
                    filename_line = False
                    filename = line[1:-1]
                    filename = os.path.splitext(filename)[0]
                    continue
                if line == '.':
                    filename_line = True
                    forest[filename] = concept_line.flushLine()
                    continue
                if line in [OPEN_PAR, CLOSING_PAR]:
                    concept_line.removeSeparator()
                    concept_line.append(line)
                else:
                    concept_line.append(line)
                if line != OPEN_PAR:
                    concept_line.addSeparator()
        finally:
            fr.close()
        return forest

    @ExScript.command
    def mlf2sgml(self, files, bucktype=None):
        """Convert input alignment of 2 Files (ref and hyp) into SCLite sgml format
        """
        try:
            ref_fn, hyp_fn = files
        except ValueError:
            raise ValueError("Command `mlf2sgml` requires exactly 2 files")

        if bucktype not in [None, 'dialog']:
            raise ValueError("Unknown bucktype: %r" % bucktype)

        ref = self.readForestFromMLF(ref_fn)
        hyp = self.readForestFromMLF(hyp_fn)

        fw = sys.stdout
        fw.write('<SYSTEM title="%s" ref_fname="%s" hyp_fname="%s" '
                 'creation_date="%s" format="2.3" frag_corr="FALSE" '
                 'opt_del="FALSE" weight_ali="FALSE" weight_filename="">\n' % \
                 (hyp_fn, ref_fn, hyp_fn, time.strftime('%a, %d %b %Y %H:%M:%S')))

        data = {}

        for fn, tree1, tree2, dist, script in self.forestProcessor(ref, hyp):
            dialog = self.dialogName(fn)
            if dialog not in data:
                data[dialog] = []
            if bucktype == 'dialog':
                data[dialog].extend(script)
            else:
                data[dialog].append(script)

        if bucktype == 'dialog':
            for key in data.keys():
                data[key] = [data[key]]
        
        for dialog, paths in data.iteritems():
            fw.write('<SPEAKER id="%s">\n' % dialog)
            i = 0
            for path in paths:
                id_path = '%s_%05d' % (dialog, i)
                word_cnt = len(path)
                fw.write('<PATH id="%s" word_cnt="%d" sequence="%d">\n' % \
                         (id_path, word_cnt, i))
                out = []
                for a, b in path:
                    if a == b:
                        out.append('C,"%s","%s"' % (a, b))
                    elif a == None:
                        out.append('I,,"%s"' % b)
                    elif b == None:
                        out.append('D,"%s",' % a)
                    else:
                        out.append('S,"%s","%s"' % (a, b))
                out = ':'.join(out)
                fw.write(out + '\n')
                fw.write('</PATH>\n')
                i += 1
            fw.write('</SPEAKER>\n')

        fw.write('</SYSTEM>\n')

    def forestProcessor(self, forest1, forest2, make_leaf=True):
        forest1 = forest1.copy()
        forest2 = forest2.copy()
        d = TreeDist()
        for fn in sorted(forest1.keys()):
            d.clear()
            tree1 = forest1.pop(fn)
            try:
                tree2 = forest2.pop(fn)
            except KeyError:
                self.logger.error("Semantics of %r not found in forest2", fn)
                continue
            self.logger.debug("Processing file %r", fn)
            try:
                if tree1 is None or tree2 is None:
                    raise ValueError('Bad semantics trees')
                dist, script = d.fullDist(tree1, tree2)
            except ValueError:
                self.logger.error("Error in semantics %r:", fn)
                self.logger.error("S1: %s, S2: %s", tree1, tree2)
                continue
            # Remove match of virtual root,  H(S, S)
            script.remove(((ROOT_CONCEPT,), (ROOT_CONCEPT,)))
            if make_leaf:
                script = script.leafScript
            # Call tree_processor
            yield fn, tree1, tree2, dist, script
        for fn in sorted(forest2.keys()):
            self.logger.error("Semantics of %r not found in forest1", fn)

    def loadForestFiles(self, files, only=None, skip=None):
        forests = []
        for fn in files:
            f = self.readForestFromMLF(fn, only, skip)
            forests.append(f)
        return forests

    def printEditScript(self, fn, tree1, tree2, script):
        H, D, I, S = script.HDIS
        N = script.numConcepts[0]
        Corr = script.statCorr*100.
        Acc = script.statAcc*100.

        summary = 'Acc=%6.2f, Corr=%6.2f\n# H=%4d, D=%3d, S=%3d, I=%3d, N=%3d' % \
                  (Corr, Acc, H, D, S, I, N)
        script = '\n'.join(script.asString)
        sys.stdout.write('"%s"\n' % fn)
        sys.stdout.write("# Ref: %s\n" % tree1)
        sys.stdout.write("# Rec: %s\n" % tree2)
        sys.stdout.write("# %s\n" % summary)
        sys.stdout.write("%s\n.\n" % script)

    def genFnPairs(self, files, twoside=False):
        if not twoside:
            for i, f1 in enumerate(files):
                for f2 in files[i+1:]:
                    if f1 != f2:
                        yield f1, f2
        else:
            for f1 in files:
                for f2 in files:
                    if f1 != f2:
                        yield f1, f2

    @ExScript.command
    def editscripts(self, files):
        """Print edit-script, use 2 input sets: test, system_output
        """
        if len(files) != 2:
            raise ValueError("You must supply 2 input files for `editscripts` command")
        
        forest1, forest2 = self.loadForestFiles(files)
        for fn, tree1, tree2, dist, script in self.forestProcessor(forest1, forest2):
            self.printEditScript(fn, tree1, tree2, script)

    def groupMapping(self, fn, type):
        if type == 'none':
            return fn
        elif type == 'dlg':
            return fn.split('_', 1)[0]
        else:
            raise ValueError("Unknown grouping: %s" % type)

    @ExScript.command
    def sresults(self, files, fw=sys.stdout, only=[], skip=[], twoside=False, groupby='none'):
        """Print HResults-like statistics of system's output
        """

        if not only:
            only = None
        if not skip:
            skip = None

        tH = tD = tS = tI = tN = 0
        uH = uN = 0
        tHit = ADict()
        tMiss = ADict()
        tFA = ADict()

        strftime = time.strftime('%a, %d %b %Y %H:%M:%S')

        fw.write('----------------------- Semantics Scores --------------------------\n')

        for fn1, fn2 in self.genFnPairs(files, twoside):
            forest1, forest2 = self.loadForestFiles((fn1, fn2), only, skip)
            fw.write('====================== CDC Results Analysis =======================\n')
            fw.write('  Date: %s\n' % strftime)
            fw.write('  Ref : %s\n' % fn1)
            fw.write('  Rec : %s\n' % fn2)
            fw.write('-------------------------- File Results ---------------------------\n')

            processor = self.forestProcessor(forest1, forest2)

            H = N = D = I = S = 0
            last_group = None
            for fn, tree1, tree2, dist, script in processor:
                new_group = self.groupMapping(fn, groupby)
                if last_group is None:
                    last_group = new_group
                if new_group != last_group:
                    # Doslo ke zmene skupiny, vypisu charakteristiky
                    if N != 0:
                        Corr = (float(H)/N)*100.
                        Acc = (float(H-I)/N)*100.
                    else:
                        Corr = Acc = 0.

                    fw.write('%s:  %6.2f(%6.2f)  [H=%4d, D=%3d, S=%3d, I=%3d, N=%3d]\n' % \
                             (last_group, Corr, Acc, H, D, S, I, N))
                    tH += H; tD += D; tS += S;
                    tI += I; tN += N
                    if S == 0 and I == 0 and D == 0:
                        assert H == N
                        uH += 1
                    uN += 1

                    # Vynulovani prubeznych skupinovych charakteristik
                    H = N = D = I = S = 0
                    # Nastaveni nove skupiny
                    last_group = new_group

                lH, lD, lI, lS = script.HDIS
                H += lH
                D += lD
                I += lI
                S += lS
                N += script.numConcepts[0]

                hit, miss, fa = script.hitMissFA
                tHit += hit
                tMiss += miss
                tFA += fa
        else:
            # Vypsani za posledni skupinu
            if N != 0:
                Corr = (float(H)/N)*100.
                Acc = (float(H-I)/N)*100.
            else:
                Corr = Acc = 0.

            fw.write('%s:  %6.2f(%6.2f)  [H=%4d, D=%3d, S=%3d, I=%3d, N=%3d]\n' % \
                     (last_group, Corr, Acc, H, D, S, I, N))
            tH += H; tD += D; tS += S;
            tI += I; tN += N
            if S == 0 and I == 0 and D == 0:
                assert H == N
                uH += 1
            uN += 1

        tCorr = 100. * tH / tN
        tAcc = 100. * (tH - tI) / tN
        uS = uN - uH
        uCorr = 100. * uH / uN

        fw.write('------------------------ Concept Results --------------------------\n')
        allConcepts = (tHit+tMiss+tFA).keys()
        allResults = []
        for concept in sorted(allConcepts):
            C = float(tHit[concept])
            FA = float(tFA[concept])
            M = float(tMiss[concept])
            if C+FA > 0:
                Prec = C / (C+FA) * 100
            else:
                Prec = 0
            if C+M > 0:
                Recall = C / (C+M) * 100
            else:
                Recall = 0
            if Prec+Recall > 0:
                F = 2*Prec*Recall/(Prec+Recall)
            else:
                F = 0
            allResults.append((F, concept, Prec, Recall, C, M, FA))

        for F, concept,Prec, Recall, C, M, FA in sorted(allResults, reverse=True):
            fw.write('%-15s: F=%6.2f, P=%6.2f, R=%6.2f [C=%d, M=%d, FA=%d]\n' % (concept, F, Prec, Recall, C, M, FA))

        tC = float(tHit.sum())
        tM = float(tMiss.sum())
        tFA = float(tFA.sum())

        tPrec = tC / (tC+tFA) * 100
        tRecall = tC / (tC+tM) * 100
        tF = 2*tPrec*tRecall/(tPrec+tRecall)

        fw.write('------------------------ Overall Results --------------------------\n')
        fw.write('UTTR: %%Correct=%.2f [H=%d, S=%d, N=%d]\n' % (uCorr, uH, uS, uN))
        fw.write('CONC: F=%.2f, P=%.2f, R=%.2f [C=%d, M=%d, FA=%d]\n' % (tF, tPrec, tRecall, tC, tM, tFA))
        fw.write('      %%Corr=%.2f, Acc=%.2f [H=%d, D=%d, S=%d, I=%d, N=%d]\n' % (tCorr, tAcc, tH, tD, tS, tI, tN))
        fw.write('===================================================================\n')


        ret = {}
        ret['cCorr'] = tCorr
        ret['cAcc'] = tAcc
        ret['cH'] = tH
        ret['cD'] = tD
        ret['cS'] = tS
        ret['cI'] = tI
        ret['cN'] = tN
        ret['uCorr'] = uCorr
        ret['uH'] = uH
        ret['uS'] = uS
        ret['uN'] = uN
        ret['Prec'] = tPrec
        ret['Recall'] = tRecall
        ret['F'] = tF
        return ret

    def dialogName(self, fn):
        try:
            under_index = fn.rindex('_')
        except IndexError:
            return fn
        return fn[:under_index]

    def filenameKey(self, fn, bucktype=None):
        if bucktype == 'dialog':
            return self.dialogName(fn)
        else:
            return fn

    @ExScript.command
    def signif(self, files, bucktype='none'):
        """Compute signification of 3 input sets: test, system_output1, system_output2
        """
        if len(files) != 3:
            raise ValueError("You must supply 3 input files for `signif` command")

        if bucktype not in ['none', 'dialog']:
            raise ValueError("Unknown `bucktype`: %r" % bucktype)

        self.logger.debug("Importing scipy")
        from scipy.stats import median, mean, tvar, tstd
        from scipy.stats.morestats import wilcoxon
        from scipy.stats.distributions import norm, t as t
        from scipy import sqrt

        forest1, forest2, forest3 = self.loadForestFiles(files)

        self.logger.info("Processing forests 1 and 2")

        diff1 = {}
        for fn, tree1, tree2, dist, script in self.forestProcessor(forest1, forest2):
            H, D, I, S = script.HDIS
            n_errors = D+I+S
            fn = self.filenameKey(fn, bucktype)
            diff1.setdefault(fn, 0.)
            diff1[fn] += n_errors

        self.logger.info("Processing forests 1 and 3")

        diff2 = {}
        for fn, tree1, tree2, dist, script in self.forestProcessor(forest1, forest3):
            H, D, I, S = script.HDIS
            n_errors = D+I+S
            fn = self.filenameKey(fn, bucktype)
            diff2.setdefault(fn, 0.)
            diff2[fn] += n_errors

        def mapsswe(x, y):
            xm = mean(x)
            ym = mean(y)
            s = 0.
            n = 0.
            for xi, yi in izip(w1, w2):
                s += ((xi-yi) - (xm-ym))**2
                n += 1

            t_stat = sqrt(n) * abs(xm-ym) / sqrt(s/(n-1.))
            p_value = t.sf(t_stat, n-1) * 2
            return t_stat, p_value

        Z_values = []
        w1 = []
        w2 = []
        for key in sorted(diff1.keys()):
            if key not in diff2:
                self.logger.error("Unmatched utterance: %r", key)
                continue
            Na = diff1.pop(key)
            Nb = diff2.pop(key)
            w1.append(Na)
            w2.append(Nb)
            Z_values.append(Na-Nb)

        Z_mean = mean(Z_values)
        Z_median = median(Z_values)
        Z_tvar = tvar(Z_values)
        Z_tstd = tstd(Z_values)

        wilcoxon_t_stat, wilcoxon_p_value = wilcoxon(w1, w2)

        mapsswe_w_stat, mapsswe_p_value = mapsswe(w1, w2)

        fw = sys.stdout
        fw.write("Z stats:\n")
        fw.write("========\n")
        fw.write("  - mean:     %9.3f\n" % Z_mean)
        fw.write("  - median:   %9.3f\n" % Z_median)
        fw.write("  - tvar:     %9.3f\n" % Z_tvar)
        fw.write("  - tstd:     %9.3f\n\n" % Z_tstd)
        fw.write("Wilcoxon test:\n")
        fw.write("==============\n")
        fw.write("  - p-value:  %9.3f (two-tailed) [significant if <= 0.05]\n" % wilcoxon_p_value)
        fw.write("  - t-stat:   %9.3f\n\n" % wilcoxon_t_stat)
        fw.write("MAPSSWE test:\n")
        fw.write("=============\n")
        fw.write("  - p-value:  %9.3f (two-tailed) [significant if <= 0.05]\n" % mapsswe_p_value)
        fw.write("  - t-stat:   %9.3f\n\n" % mapsswe_w_stat)

    def superForest(self, dicts):
        keys = set()
        ret = {}
        for d in dicts:
            keys |= set(d.keys())
        for k in keys:
            item = []
            for i, d in enumerate(dicts):
                try:
                    item.append(d[k])
                except KeyError:
                    self.logger.error("Tree %r not found in forest %d" % (k, i))
                    continue
            ret[k] = item
        return ret

    def matchedForestProcessor(self, forests, sort=True):
        sforest = self.superForest(forests)

        d = CommonDist()

        for fn in sorted(sforest.keys()):
            trees = sforest[fn]
            if sort:
                in_trees = sorted(trees, key=lambda obj: obj.numConcepts)
            else:
                in_trees = trees
            common = d.commonTree(*in_trees)
            yield fn, trees, common

    @ExScript.command
    def kappa(self, files, nconc=5):
        """Compute kappa statistics on Files.
        """
        forests = self.loadForestFiles(files)

        all_concepts = 0.
        all_matches = 0.

        exact_matches = 0.
        exact_total = 0.

        concept_counts = {}

        for fn, trees, common in self.matchedForestProcessor(forests):
            num_concepts = 0.
            num_matches = 0.

            exact_match = True
            first_tree = trees[0]

            for i, t in enumerate(trees):
                exact_match = exact_match and (first_tree == t)

                num_concepts += t.numConcepts - 1
                num_matches += common.numMatches - 1
                if i not in concept_counts:
                    concept_counts[i] = {}
                concept_counts[i] = utils_dict_sum(concept_counts[i], t.conceptCounts)

            if exact_match:
                exact_matches += 1
            exact_total += 1

            all_concepts += num_concepts
            all_matches += num_matches

        P_A = all_matches / all_concepts
        P_A_exact = exact_matches / exact_total

        P_E_tree = {}
        P_E_keys = set()
        for tree_num, counts in concept_counts.items():
            del counts[ROOT_CONCEPT]
            total_count = float(sum(counts.itervalues()))
            for key in counts:
                counts[key] /= total_count
                P_E_keys.add(key)
            for key in P_E_keys:
                P_E_tree[key] = P_E_tree.get(key, 1) * counts.get(key, 0)

        concept_counts['P(E)'] = P_E_tree
        P_E = sum(P_E_tree.itervalues())

        Kappa = (P_A-P_E) / (1-P_E)



        fw = sys.stdout
        fw.write('Concept counts:\n')
        fw.write('===============\n')
        for tree_num, counts in sorted(concept_counts.items()):
            fw.write('  Tree %s\n' % (tree_num,))
            fw.write('  ~~~~~~~~~~~~~~~~~~~~  ~~~~~~\n')
            for concept, count in sorted(counts.items(), key=lambda i:i[1], reverse=True)[:nconc]:
                fw.write('  %-20s  %.4f\n' % (concept, count))
            fw.write('\n')
        fw.write('\n')
        fw.write('Kappa statistics:\n')
        fw.write('=================\n')
        fw.write('  - Total number of matches:    %10d\n' % all_matches)
        fw.write('  - Total number of concepts:   %10d\n' % all_concepts)
        fw.write('  - P(A):                       %10.2f%%\n' % (P_A * 100))
        fw.write('  - P(E):                       %10.2f%%\n' % (P_E * 100))
        fw.write('  - Kappa value:                %10.2f%%\n' % (Kappa * 100))
        fw.write('\n')
        fw.write('Exact matches:\n')
        fw.write('==============\n')
        fw.write('  - Number of exact matched turns: %10d\n' % exact_matches)
        fw.write('  - Total number of turns:         %10d\n' % exact_total)
        fw.write('  - P_exact(A):                    %10.2f%%\n' % (P_A_exact * 100))

    @ExScript.command
    def matching(self, files):
        """Print matching of trees into common subtree. Trees are read from Files.
        """
        forests = self.loadForestFiles(files)

        fw = sys.stdout

        for fn, trees, common in self.matchedForestProcessor(forests):
            fw.write('"%s"\n' % fn)
            for i, t in enumerate(trees):
                fw.write("Tree %3d: %s\n" % (i, t))
            fw.write("Common:   %s\n" % common)
            fw.write(".\n")

def main():
    script = TreeDistScript()
    script.run()

if __name__ == '__main__':
    main()
