from svc.egg import PythonEgg
from svc.utils import cartezian, ADict
from svc.ui import gmtk
from svc.map import SymMap

from bisect import insort
from heapq import heappush, heappop

from math import log

DEPTH = 4
MAX_POP = 4
MAX_PUSH = 2
EMPTY_CONCEPT = '_EMPTY_'
DUMMY_CONCEPT = '_DUMMY_'

class FSMGenerator(PythonEgg):
    def __init__(self, workspace, conceptMap, symbolMaps, cutoff_sym=-1, cutoff_trans=None, max_states=None, logger=None, pteSymbols=[]):
        super(FSMGenerator, self).__init__()
        self.workspace = workspace
        self.max_states = max_states
        self.cutoff_sym = cutoff_sym
        if cutoff_trans is None:
            self.cutoff_trans = cutoff_sym
        else:
            self.cutoff_trans = cutoff_trans
        self.logger = logger
        self.conceptMap = conceptMap
        self.pteSymbols = pteSymbols
        self.pteMap = self.createPTESymbolMap(pteSymbols)
        self.symbolMaps = symbolMaps

    def createPTESymbolMap(self, pteSymbols):
        'pteSymbols - Pass-through-empty symbols'
        ret = SymMap()
        for i, sym in enumerate(pteSymbols):
            ret[sym] = i
        return ret

    def strState(self, c_t):
        if len(c_t) == 4:
            c_t = [c_t]
        ret = []
        for stack in c_t:
            ret.append('[')
            for c in stack:
                c_str = self.conceptMap.inverse[c]
                if c_str == '_EMPTY_':
                    c_str = '-'
                ret.append(c_str)
                ret.append(',')
            del ret[-1]
            ret.append(']')
        return ''.join(ret)

    def convertStateMap(self, map):
        ret = SymMap()
        for k, v in map.iteritems():
            ret[self.strState(k)] = v
        return ret

    def genStates(self):
        processed = set()
        backoff_stat = ADict(default=set)

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

        pte_map = SymMap()
        pte_map2 = SymMap()
        if self.pteMap:
            pte_symbols = sorted(self.pteMap.values())
            for key, value in sorted(self.pteMap.items()):
                pte_map[value] = value+count
                pte_map2[key] = value+count
            count += len(pte_map)
        else:
            pte_symbols = []

        for map in self.symbolMaps:
            if map is None:
                map = {}
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
        s0_expanded = False

        cutoff_sym = self.cutoff_sym
        cutoff_trans = self.cutoff_trans
        max_states = self.max_states

        logger = self.logger

        stack = [(0, 0, s0)]
        stack_set = set([s0])

        state_map = SymMap()
        state_map[s0] = 0

        _pop_ = self._pop_
        interim_counter = 0

        n_arcs = 0
        while stack:
            if max_states is None:
                total_states = len(state_map) - interim_counter
            else:
                total_states = max_states
            if logger is not None:
                logger.debug('   #states (unexpanded/total) %.2f%%, %d/%d, #arcs %d', 100.*len(processed)/total_states, total_states-len(processed), total_states, n_arcs)

            c_t_backoff, c_t_dist, c_t = stack.pop(0)
            backoff_stat[c_t_backoff].add(c_t)
            if logger is not None:
                logger.debug('     %.2f: %s, backoff=%d', c_t_dist, self.strState(c_t), c_t_backoff)
            state_c_t = state_map[c_t]
            processed.add(c_t)
            stack_set.remove(c_t)

            ret = []

            pop_pmf = list(pop_Given_C[: c_t[0], c_t[1], c_t[2], c_t[3]])
            push_pmf = list(push_Given_C[: c_t[0], c_t[1], c_t[2], c_t[3]])

            for pop in range(0, MAX_POP+1):
                prob_pop = pop_pmf[pop]

                if prob_pop <= cutoff_trans:
                    continue

                interim_counter += 1
                c_inter = c_t[pop:] + (_EMPTY_, ) * pop
                osym = ')'*pop
                if not osym:
                    osym = 'epsilon'
                ret.append( (prob_pop, c_t, (c_t, c_inter), _pop_, osym) )

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
                        osym = ''
                        for push_concept in reversed(to_push):
                            osym += conceptMap.inverse[push_concept]+'('
                        if not osym:
                            osym = 'epsilon'

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

                        prob_trans = prob_push * prob_new_c
                        # Do cut-off
                        if prob_trans <= cutoff_trans:
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

                        if c_new not in processed and c_new not in stack_set:
                            stack_set.add(c_new)
                            c_new_dist = (c_t_dist-log(prob_trans))
                            insort(stack, (backoff, c_t_dist-log(prob_trans), c_new))

                        c_next = (c_t, c_inter)

                        if pte_symbols and c_inter == (_EMPTY_,)*4 and push != 0:
                            for pte_sym in pte_symbols:
                                prob_ptesym = 1.0
                                pte_sym = pte_map[pte_sym]
                                pte_osym = pte_map2.inverse[pte_sym]
                                ret.append( (prob_trans*prob_ptesym, c_next, c_new, pte_sym, pte_osym) )
                            prob_trans = 1.0
                            c_next = c_new

                        for sym, map, pmf in zip(symbols, maps, s_pmf):
                            if map is None:
                                continue

                            for isym in sym:
                                prob_isym = pmf[isym]

                                # Do cut-off
                                if prob_isym <= cutoff_sym:
                                    continue
                                else:
                                    isym = map[isym]
                                    ret.append( (prob_trans*prob_isym, c_next, c_new, isym, osym) )

                            # For symbols other than the first
                            prob_trans = 1.0
                            c_next = c_new
                            osym = 'epsilon'

            for prob, c_t, c_new, isym, osym in ret:
                state_c_new = state_map.add(c_new)
                state_c_t = state_map.add(c_t)

                osym = osym_map.add(osym)

                n_arcs += 1

                yield state_c_t, state_c_new, isym, osym, prob

            if max_states is not None and len(processed) >= max_states:
                break

        self.stateMap = self.convertStateMap(state_map)
        self.osymMap = osym_map
        self.isymMaps = maps2
        self.ipteMap = pte_map2

        backoff_stat = ADict((k, len(v)) for (k,v) in backoff_stat.iteritems())

        if logger is not None:
            logger.debug('Backoff statistics:')
            logger.debug('===================')
            total = backoff_stat.sum()
            for key, value in sorted(backoff_stat.items()):
                logger.debug('  backoff=%d: #%d (%.2f%%)', key, value, 100.*value/total)

    def genPadder(self):
        symbols = []
        maps2 = []
        count = 1
        _pop_ = 0

        if self.pteMap:
            pte_symbols = sorted(self.pteMap.values())
            pte_map = SymMap()
            pte_map2 = SymMap()
            for key, value in sorted(self.pteMap.items()):
                pte_map[value] = value+count
                pte_map2[key] = value+count
                _pop_ = max(_pop_, value+count)
            count += len(pte_map)
        else:
            pte_symbols = []
            pte_map = {}
            pte_map2 = {}

        for map in self.symbolMaps:
            if map is None:
                map = {}
            symbols.append(sorted(map.values()))
            new_map = SymMap()
            new_map2 = SymMap()
            for key, value in sorted(map.items()):
                new_map[value] = value+count
                new_map2[key] = value+count
                _pop_ = max(_pop_, value+count)
            count += len(new_map)
            maps2.append(new_map2)

        _pop_ += 1

        n_sets = sum(1 for i in maps2 if len(i)!=0)
        p_sets = 0

        end_state = 0
        state = 1
        yield end_state, state, 0, _pop_

        for key, value in sorted(pte_map.items()):
            yield state, state, value, value

        for map in maps2:
            if len(map) == 0:
                continue
            p_sets += 1
            if p_sets == n_sets:
                new_state = end_state
            else:
                new_state = state + 1
            for key, value in sorted(map.items()):
                yield state, new_state, value, value
            state += 1

        self._pop_ = _pop_

    def genRepeater(self):
        symbols = []
        maps2 = []
        count = 1

        if self.pteMap:
            pte_symbols = sorted(self.pteMap.values())
            pte_map = SymMap()
            pte_map2 = SymMap()
            for key, value in sorted(self.pteMap.items()):
                pte_map[value] = value+count
                pte_map2[key] = value+count
            count += len(pte_map)
        else:
            pte_symbols = []
            pte_map = {}
            pte_map2 = {}

        for map in self.symbolMaps:
            if map is None:
                map = {}
            symbols.append(sorted(map.values()))
            new_map = SymMap()
            new_map2 = SymMap()
            for key, value in sorted(map.items()):
                new_map[value] = value+count
                new_map2[key] = value+count
            count += len(new_map)
            maps2.append(new_map2)

        end_state = state = 0
        state_map = SymMap()
        if pte_map2:
            for value in pte_map2.values():
                state += 1
                yield end_state, state, value, value
                yield state, state, 0, value
                for map in maps2:
                    for sym in map.values():
                        yield state, state, sym, sym
                yield state, end_state, 0, 0
        else:
            for map in maps2:
                for sym in map.values():
                    yield state, state, sym, sym


    def writeFSM(self, fn):
        fw = file(fn, 'w')
        n_arcs = 0
        try:
            for state_0, state_1, input, output, prob in self.genStates():
                try:
                    print >> fw, '%d\t%d\t%d\t%d\t%e' % (state_0, state_1, input, output, -log(prob))
                except OverflowError:
                    print >> fw, '%d\t%d\t%d\t%d\t%e' % (state_0, state_1, input, output, 1e100)
                n_arcs += 1
            print >> fw, '0'
        finally:
            fw.close()
        if self.logger is not None:
            self.logger.debug('Writen FSM with %d states, %d arcs', len(self.stateMap), n_arcs)

    def writeFSMPadder(self, fn):
        fw = file(fn, 'w')
        n_arcs = 0
        try:
            for state_0, state_1, input, output in self.genPadder():
                print >> fw, '%d\t%d\t%d\t%d' % (state_0, state_1, input, output)
                n_arcs += 1
            print >> fw, '0'
        finally:
            fw.close()
        if self.logger is not None:
            self.logger.debug('Writen FSM padder with %d arcs', n_arcs)

    def writeFSMRepeater(self, fn):
        fw = file(fn, 'w')
        n_arcs = 0
        try:
            states = set()
            for state_0, state_1, input, output in self.genRepeater():
                print >> fw, '%d\t%d\t%d\t%d' % (state_0, state_1, input, output)
                states.add(state_0)
                states.add(state_1)
                n_arcs += 1
            for i in states:
                print >> fw, i
        finally:
            fw.close()
        if self.logger is not None:
            self.logger.debug('Writen FSM padder with %d arcs', n_arcs)

