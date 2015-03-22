HOW-TO convert the trained GMTK semantic parser into Finite State Machine (FSM)

# Step 1. - training the EHVS parser #

First of all, you will need the trained semantic parser. You can train it using the code published [here](http://code.google.com/p/extended-hidden-vector-state-parser/source/checkout) and using the following command:

`./semantics.py all`

I have used the "shorter" variant, which uses only 5% of available data to shorter the training time:

`./semantics.py --cfgfile etc/settings.small -vvv --debug all -s DATA_REDUCTION=5 -s TRAIN_EM_ITERS=3`

The output of the training process looks like:

```
Running external method SemanticsMain.makeDirs ('bin/semantics/makeDirs')
Running external method SemanticsMain.deleteTmpData ('bin/semantics/deleteTmpData')
Running external method SemanticsMain.setCommonParams ('bin/semantics/setCommonParams')
Running external method SemanticsMain.copyXMLData ('bin/semantics/copyXMLData')
Running external method SemanticsMain.genInputMaps ('bin/semantics/genInputMaps')
OOV rate per symbol:
===================:
    S1: 4.95%
    S2: 0.00%
    S3: 0.00%
Running external method SemanticsMain.genInputs ('bin/semantics/genInputs')
Running external method SemanticsMain.genHiddenObservation ('bin/semantics/genHiddenObservation')
Running external method SemanticsMain.genEndOfUtteranceObservation ('bin/semantics/genEndOfUtteranceObservation')
Running external method SemanticsMain.initSemanticModel ('bin/semantics/initSemanticModel')
Running external method SemanticsMain.initLexicalModel ('bin/semantics/initLexicalModel')
Running external method SemanticsMain.triangulate ('bin/semantics/triangulate')
Running external method SemanticsMain.trainModel ('bin/semantics/trainModel')
Running external method SemanticsMain.forcealignTrn ('bin/semantics/forcealignTrn')
SemanticsMain.forcealignTrn: <built-in>:0: fatal error: when writing output to : Přerušena roura (SIGPIPE)
SemanticsMain.forcealignTrn: compilation terminated.
SemanticsMain.forcealignTrn: WARNING: Can't close pipe 'cpp build/2008-06-16-13.09/gen/tri/semantics_fa_trn.str.tri'.
Results:
========
    Concept Accuracy          : 100.00
    Concept Correctness       : 100.00
    Utterance Correctness     : 100.00
Running external method SemanticsMain.smoothModel ('bin/semantics/smoothModel')
SemanticsMain.smoothModel: <built-in>:0: fatal error: when writing output to : Přerušena roura (SIGPIPE)
SemanticsMain.smoothModel: compilation terminated.
SemanticsMain.smoothModel: WARNING: Can't close pipe 'cpp build/2008-06-16-13.09/gen/tri/semantics_smth.str.tri'.
Running external method SemanticsMain.scaleModel ('bin/semantics/scaleModel')
Running external method SemanticsMain.decodeHldt ('bin/semantics/decodeHldt')
SemanticsMain.decodeHldt: <built-in>:0: fatal error: when writing output to : Přerušena roura (SIGPIPE)
SemanticsMain.decodeHldt: compilation terminated.
SemanticsMain.decodeHldt: WARNING: Can't close pipe 'cpp build/2008-06-16-13.09/gen/tri/semantics_dcd.str.tri'.
Results:
========
    Concept Accuracy          :  38.00
    Concept Correctness       :  46.00
    Utterance Correctness     :  50.94
Running external method SemanticsMain.decodeTst ('bin/semantics/decodeTst')
SemanticsMain.decodeTst: <built-in>:0: fatal error: when writing output to : Přerušena roura (SIGPIPE)
SemanticsMain.decodeTst: compilation terminated.
SemanticsMain.decodeTst: WARNING: Can't close pipe 'cpp build/2008-06-16-13.09/gen/tri/semantics_dcd.str.tri'.
Results:
========
    Concept Accuracy          :  37.10
    Concept Correctness       :  50.23
    Utterance Correctness     :  45.67
Generating output XMLs for: fa_trn
Generating output XMLs for: dcd_hldt
Generating output XMLs for: dcd_tst
Running external method SemanticsMain.moveResults ('bin/semantics/moveResults 1')
SemanticsMain.moveResults: Copying files from build/2008-06-16-13.09 into results/2008-06-16-13.09
```

This will run the complete training process and it creates the subdirectory in the `results` directory. This subdirectory contains the parameters of the trained EHVS parser such as symbol maps and conditional probability table parameters. The subdirectories of `results` directory are named by the date and time the command was executed. In my case, the parameters was stored in the directory `results/2008-06-16-13.09`. The name of the directory is showed on the last line of the output from `semantics.py all` command.

# Step 2. - converting the EHVS parser into FSM #

The conversion is done using the `semantics.py` script. This script supports many commands (like `all` in the section above). One of these commands is the `fsmconvert` command, which converts the trained model into Finite State Machine.

**Note:** The conversion into FSM requires, that you have the same `settings` and `settings.path` files which you have used for training!

The command which executes the conversion into FSM looks like:

`REUSE_BUILD_DIR=results/2008-06-16-13.09  ./semantics.py fsmconvert -vvv`

where the `REUSE_BUILD_DIR` part is interpreted by the shell. It sets the environment variable which points to the directory with the trained model (remember the `results/2008-06-16-13.09` directory mentioned above?). The `-vvv` option sets the verbose flags so you can see the progress of FSM creation:

```
Running external method SemanticsMain.setCommonParams ('bin/semantics/setCommonParams')
Reading concept map: results/2008-06-16-13.09/maps/concept.map
Reading s1 map: results/2008-06-16-13.09/maps/s1.map
Dataset s2 is turned off
Dataset s3 is turned off
Reading master file: params/mstr/dcd/in.mstr
Creating FSM from arcs
Total number of concepts: 34
Writen FSM padder with 453 arcs
Writen FSM padder with 454 arcs
   #states (unexpanded/total) 0.00%, 200/200, #arcs 0
     0.00: [-,-,-,-], backoff=0
   #states (unexpanded/total) 0.50%, 199/200, #arcs 6333
     1.63: [TIME,-,-,-], backoff=0
   #states (unexpanded/total) 1.00%, 198/200, #arcs 12762
     1.88: [DEPARTURE,-,-,-], backoff=0
   #states (unexpanded/total) 1.50%, 197/200, #arcs 13245
     1.99: [ACCEPT,-,-,-], backoff=0
   #states (unexpanded/total) 2.00%, 196/200, #arcs 13324
     2.18: [GREETING,-,-,-], backoff=0
   #states (unexpanded/total) 2.50%, 195/200, #arcs 20548
     2.78: [ARRIVAL,-,-,-], backoff=0
...
   #states (unexpanded/total) 99.50%, 1/200, #arcs 1094147
     37.95: [_DUMMY_,FROM,REF,ARRIVAL], backoff=3
Backoff statistics:
===================
  backoff=0: #40 (20.00%)
  backoff=1: #3 (1.50%)
  backoff=2: #46 (23.00%)
  backoff=3: #111 (55.50%)
Writen FSM with 832 states, 1103304 arcs
Running external method SemanticsMain.fsmcompile ('bin/semantics/fsmcompile')
```

This command creates some files in the `results/2008-06-16-13.09/fsm` directory. These file are subsequently used by the `hvsparser.py` command.

# Step 3. - parsing using the FSM model #

There is the simple script named `hvsparser.py` which loads the converted FSM model, parses its standard input using the FSM model, and outputs the parse tree to its output. The invocation of this command is simple:

`./hvsparser.py results/2008-06-16-13.09/fsm`

You can type some input or you can redirect the stdin and stdout streams using your shell. To process the whole directory of XML files, you can use the command:

`./hvsparser.py results/2008-06-16-13.09/fsm --xml-dir DIR_WITH_XML --skip-empty --mlf --omit-leaves`

where `DIR_WITH_XML` is the directory with dialogue XML files, `--skip-empty` instructs the HVS parser to skip dialogue acts with empty semantics, if `--mlf` is used, the output is in the MLF format and if `--omit-leaves` is used, the `--mlf` does NOT contain the word-level alignment and is suitable for the `cdc-treedist.py` tool.

# Step 4. - setting the conversion parameters #

In the `settings` file there are three options which controls the conversion process:

  * FSM\_STATES - the maximum number of states (stacks) to expand (first the most probable states (hiden vector states) are expanded. The probabiliti of a HVS is given the probability of the path from the state zero '[-,-,-,-]. Typcal value might be about 1000 states.
  * FSM\_CUTOFF\_SYM and FSM\_CUTOFF\_TRANS - the thresholds for probability of transitions. The typycal values might be '1e-10'




# Step 5. - using it in the batch #

To convert the model into FSM in the batch file, you can add the call of `fsmconvert()` at the end of your batch.