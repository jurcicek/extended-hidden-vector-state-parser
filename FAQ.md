Frequently Asked Questions

# Question 1 #

We have a question regarding the CPT tablesWe are currently trying to find ways to write the various probability tables in a concise way, e.g. P(word|c1,c2,c3,c4), without having to write card\_word\*card\_concept^4 values. You seem to use GMTK's sparseCPTs, with only 207 different stack configurations. How do you reduce the state space this much? I'm sure your code explains this somewhere, but we didn't really understand this part.

## Answer ##

You are right. We use sparseCPTs.

The overall training is divided into training and smoothing.

During training, we get sparseCPT representing P(word|c1,c2,c3,c4). And it might be possible that you see only 207 quadruples of c1,c2,c3,c4. As a result you have series problems with data sparseness.

To deal with it, we implement simple back-off model for decoding.  From the probability P(word|c1,c2,c3,c4), we compute probabilities:
```
P(word|c1,c2,c3,c4)
P(word|c1,c2,c3)
P(word|c1,c2)
P(word|c1)
P(word)
```
See http://filip.jurcicek.googlepages.com/jurcicek07statistical.pdf page 73. The probability P(wt|ct[1, 4]) is the given
```
P(w|ct[1, 4]) if C(c[1, 4]) > 8,
P(w|ct[1, 3]) if C(c[1, 3]) > 6,
P(w|ct[1, 2]) if C(c[1, 2]) > 4,
P(w|ct[1]) if C(c[1]) > 2,
P(w) otherwise
```
We use switching between these probabilities. If we need to generate c1,c2,c3,c4 which we did not seen in the training data (filter this by number of occurrences - in this case 8), we switch to the probability P(word|c1,c2,c3). If c1,c2,c3 which was not seen in the training data (or was seen less times than 6), than we switch to the probability P(word|c1,c2,c3) and so on.

This implementation of back-off model is only a shortcut. We know that it is not likely to sum to 1 over all observation of c1,c2,c3,c4 for a word w. But it works.
So the idea is that you should not look only at P(word|c1,c2,c3,c4), but also P(word|c1,c2,c3), P(word|c1,c2), etc. And all together it is during decoding able to assign probability to any combination of w, c1,c2,c3,c4
Check  http://code.google.com/p/extended-hidden-vector-state-parser/source/browse/trunk/semantics-4/params/str/symbols/generic_symbol.str
especially this part

```
#elif defined(SYMBOL_SMOOTH) && !defined(FORCE_ALIGN)

    %------------------------%
    %  Using full smoothing  %
    %------------------------%

    variable: SYMBOL_NAME {
        type:
            discrete observed SYMBOL_INDEX:SYMBOL_INDEX cardinality SYMBOL_CARD;
        switchingparents:
            backoffSymbolsGivenC1C2C3C4(0) using mapping("copy");
        conditionalparents:
              concept1(0),concept2(0),concept3(0),concept4(0)   using SparseCPT(_CPT_4)
            | concept1(0),concept2(0),concept3(0)               using SparseCPT(_CPT_3)
            | concept1(0),concept2(0)                           using SparseCPT(_CPT_2)
            | concept1(0)                                       using  DenseCPT(_CPT_1)
            | nil                                               using  DenseCPT(_CPT_0);
    }
    
#else
```

The variable backoffSymbolsGivenC1C2C3C4 defines what sCPT or dCPT is used.

```
#if defined(SMOOTH_SYMBOLS) && !defined(FORCE_ALIGN)
    variable: backoffSymbolsGivenC1C2C3C4 {
        type:
            discrete hidden cardinality BACKOFF_C1C2C3C4_CARD;
        switchingparents:
            nil;
        conditionalparents: 
            concept1(0),concept2(0),concept3(0),concept4(0) using DeterministicCPT("backoffC1C2C3C4");
    }
#endif
```

Script http://extended-hidden-vector-state-parser.googlecode.com/svn/trunk/semantics-4/src/smoothSymbolGivenC1C2C3C4.py generate the necessary sCPT and dCPT.

Also, take a look at http://extended-hidden-vector-state-parser.googlecode.com/svn/trunk/semantics-4/src/backoffC1C2C3C4.py