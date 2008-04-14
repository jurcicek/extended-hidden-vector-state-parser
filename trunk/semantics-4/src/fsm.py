from svc.egg import PythonEgg
from svc.utils import cartezian
from svc.ui import gmtk
from svc.map import SymMap

from math import log

DEPTH = 4
MAX_POP = 4
MAX_PUSH = 2
EMPTY_CONCEPT = '_EMPTY_'
DUMMY_CONCEPT = '_DUMMY_'

class FSMGenerator(PythonEgg):
    def __init__(self, workspace, conceptMap, symbolMaps, cutoff=-1, trans_cutoff=None, logger=None):
        super(FSMGenerator, self).__init__()
        self.workspace = workspace
        self.cutoff = cutoff
        if trans_cutoff is None:
            self.trans_cutoff = cutoff
        else:
            self.trans_cutoff = trans_cutoff
        self.logger = logger
        self.conceptMap = conceptMap
        self.symbolMaps = symbolMaps

    def genStates(self):
        processed = set()

        osym_map = SymMap()
        osym_map['epsilon'] = 0

        pop_Given_C = self.workspace[gmtk.SCPT, 'popGivenC1C2C3C4']
        push_Given_C = self.workspace[gmtk.SCPT, 'pushGivenC1C2C3C4']

        c1_Given_C234 = self.workspace[gmtk.SCPT, 'concept1GivenC2C3C4']
        c1_Given_C23 = self.workspace[gmtk.SCPT, 'concept1GivenC2C3']
        c1_Given_C2 = self.workspace[gmtk.DCPT, 'concept1GivenC2']
        c1_backoff = self.workspace[gmtk.DT, 'backoffC2C3C4']
        c2_Given_C = self.workspace[gmtk.SCPT, 'concept2GivenC3C4']

        s1_Given_C1234 = self.workspace[gmtk.SCPT, 's1GivenC1C2C3C4']
        s1_Given_C123 = self.workspace[gmtk.SCPT, 's1GivenC1C2C3']
        s1_Given_C12 = self.workspace[gmtk.SCPT, 's1GivenC1C2']
        s1_Given_C1 = self.workspace[gmtk.DCPT, 's1GivenC1']
        s1_Unigram = self.workspace[gmtk.DCPT, 's1Unigram']
        s1_backoff = self.workspace[gmtk.DT, 'backoffC1C2C3C4']

        s2_Given_C1234 = self.workspace[gmtk.SCPT, 's2GivenC1C2C3C4']
        s2_Given_C123 = self.workspace[gmtk.SCPT, 's2GivenC1C2C3']
        s2_Given_C12 = self.workspace[gmtk.SCPT, 's2GivenC1C2']
        s2_Given_C1 = self.workspace[gmtk.DCPT, 's2GivenC1']
        s2_Unigram = self.workspace[gmtk.DCPT, 's2Unigram']

        s3_Given_C1234 = self.workspace[gmtk.SCPT, 's3GivenC1C2C3C4']
        s3_Given_C123 = self.workspace[gmtk.SCPT, 's3GivenC1C2C3']
        s3_Given_C12 = self.workspace[gmtk.SCPT, 's3GivenC1C2']
        s3_Given_C1 = self.workspace[gmtk.DCPT, 's3GivenC1']
        s3_Unigram = self.workspace[gmtk.DCPT, 's3Unigram']

        conceptMap = self.conceptMap
        _EMPTY_ = conceptMap[EMPTY_CONCEPT]
        _DUMMY_ = conceptMap.get(DUMMY_CONCEPT, None)
        allConcepts = sorted(conceptMap.values())

        symbols = []
        maps = []
        maps2 = []
        count = 1
        for map in self.symbolMaps:
            symbols.append(sorted(map.values()))
            new_map = SymMap()
            new_map2 = SymMap()
            for key, value in sorted(map.items()):
                new_map[value] = value+count
                new_map2[key] = value+count
            count += len(new_map)
            maps.append(new_map)
            maps2.append(new_map2)
        
        s0 = (_EMPTY_,)*4

        cutoff = self.cutoff
        trans_cutoff = self.trans_cutoff

        logger = self.logger

        stack = set([s0])

        state_map = SymMap()
        state_map[s0] = 0

        n_arcs = 0
        while stack:
            if logger is not None:
                self.logger.debug('   #states (unexpanded/total) %d/%d, #arcs %d', len(stack), len(state_map), n_arcs)

            c_t = min(stack)
            stack.remove(c_t)
            state_c_t = state_map[c_t]

            ret = {}

            pop_pmf = list(pop_Given_C[: c_t[0], c_t[1], c_t[2], c_t[3]])
            push_pmf = list(push_Given_C[: c_t[0], c_t[1], c_t[2], c_t[3]])

            for pop in range(0, MAX_POP+1):
                prob_pop = pop_pmf[pop]

                c_inter = c_t[pop:] + (_EMPTY_, ) * pop

                for push in range(0, MAX_PUSH+1):
                    prob_push = push_pmf[push]

                    if push == 0:
                        to_push_all = [()]
                    else:
                        to_push_all = cartezian(*[allConcepts]*push)

                    for to_push in to_push_all:
                        c_new = (to_push + c_inter)[:DEPTH]

                        if (c_t == c_new) and not (push == pop == 0):
                            continue

                        if _DUMMY_ in c_new[1:]:
                            continue

                        # Output symbol
                        osym = ')'*pop
                        for push_concept in reversed(to_push):
                            osym += conceptMap.inverse[push_concept]+'('
                        if not osym:
                            osym = '_'

                        # Smoothing
                        backoff = c1_backoff[c_new[1], c_new[2], c_new[3]]
                        if backoff == 0:
                            c1_pmf = c1_Given_C234[: c_new[1], c_new[2], c_new[3]]
                        elif backoff == 1:
                            c1_pmf = c1_Given_C23[: c_new[1], c_new[2]]
                        else:
                            c1_pmf = c1_Given_C2[: c_new[1]]
                        c2_pmf = c2_Given_C[: c_new[2], c_new[3]]

                        if push == 0:
                            prob_new_c = 1.0
                        elif push == 1:
                            prob_new_c = c1_pmf[to_push[0]]
                        elif push == 2:
                            prob_new_c = c1_pmf[to_push[0]] * c2_pmf[to_push[1]]

                        prob_trans = prob_pop * prob_push * prob_new_c
                        # Do cut-off
                        if prob_trans < trans_cutoff:
                            continue

                        # Smoothing
                        backoff = s1_backoff[c_new[0], c_new[1], c_new[2], c_new[3]]
                        if backoff == 0:
                            s_pmf = [list(s1_Given_C1234[: c_new[0], c_new[1], c_new[2], c_new[3]]),
                                     list(s2_Given_C1234[: c_new[0], c_new[1], c_new[2], c_new[3]]),
                                     list(s3_Given_C1234[: c_new[0], c_new[1], c_new[2], c_new[3]])]
                        elif backoff == 1:
                            s_pmf = [list(s1_Given_C123[: c_new[0], c_new[1], c_new[2]]),
                                     list(s2_Given_C123[: c_new[0], c_new[1], c_new[2]]),
                                     list(s3_Given_C123[: c_new[0], c_new[1], c_new[2]])]
                        elif backoff == 2:
                            s_pmf = [list(s1_Given_C12[: c_new[0], c_new[1]]),
                                     list(s2_Given_C12[: c_new[0], c_new[1]]),
                                     list(s3_Given_C12[: c_new[0], c_new[1]])]
                        elif backoff == 3:
                            s_pmf = [list(s1_Given_C1[: c_new[0]]),
                                     list(s2_Given_C1[: c_new[0]]),
                                     list(s3_Given_C1[: c_new[0]])]
                        else:
                            s_pmf = [list(s1_Unigram),
                                     list(s2_Unigram),
                                     list(s3_Unigram)]

                        c_next = c_t
                        for sym, map, pmf in zip(symbols, maps, s_pmf):
                            for isym in sym:
                                prob_isym = pmf[isym]

                                # Do cut-off
                                if prob_isym < cutoff:
                                    continue
                                else:
                                    isym = map[isym]
                                    ret[c_next, c_new, isym, osym] = prob_trans * prob_isym

                            # For symbols other than the first
                            prob_trans = 1.0
                            c_next = c_new
                            osym = '_'

            processed.add(c_t)

            for (c_t, c_new, isym, osym), prob in ret.iteritems():
                state_c_new = state_map.add(c_new)
                state_c_t = state_map[c_t]

                osym = osym_map.add(osym)

                n_arcs += 1

                yield state_c_t, state_c_new, isym, osym, prob
                stack.add(c_new)

            stack -= processed

        self.stateMap = state_map
        self.osymMap = osym_map
        self.isymMaps = maps2

    def writeFSM(self, fn):
        fw = file(fn, 'w')
        n_arcs = 0
        try:
            for state_0, state_1, input, output, prob in self.genStates():
                print >> fw, '%d\t%d\t%d\t%d\t%e' % (state_0, state_1, input, output, -log(prob))
                n_arcs += 1
            print >> fw, '0'
        finally:
            fw.close()
        if self.logger is not None:
            self.logger.debug('Writen FSM with %d states, %d arcs', len(self.stateMap), n_arcs)
