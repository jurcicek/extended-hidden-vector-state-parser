This chapter presents the basic concepts used in our implementation of the parser.

# Requirements #

To run our scripts, you will need working
  * Linux environment, Python (minimum v 2.4),
  * GMTK  (http://ssli.ee.washington.edu/~bilmes/gmtk/)
    * version 2009 is not working!
    * version March 2006 is OK: http://ssli.ee.washington.edu/~bilmes/gmtk/linux/2006/WedMar1_2006/
  * envsubst command (on Debian it is part of gettext-base package)
  * scipy

# Installation #

Checkout the project into your home directory. The name of the directory for the extended HVS parser should be `extended-HVS-parser`. If you want to have read/write access to the project SVN tree use the following command (you also have to be a contributor in this project)
```
svn checkout https://extended-hidden-vector-state-parser.googlecode.com/svn/trunk extended-HVS-parser --username YOUR-USER-NAME -r 108
```
or
```
svn checkout http://extended-hidden-vector-state-parser.googlecode.com/svn/trunk extended-HVS-parser -r 108
```
the read-only version.

**The [revision 108](https://code.google.com/p/extended-hidden-vector-state-parser/source/detail?r=108) is the latest working version. The code on the HEAD is not working.**

# Full run example #

Go to the directory "~/extended-HVS-parser/semantics-4":
```
cd ~/extended-HVS-parser/semantics-4
```

Run command from the bash command line:
```
./semantics.py all -vvv
```

You can also use the shortcut command:
```
./_full_run_example
```

You should see the following output:
```
Út čen 17 15:04:52 CEST 2008
Running external method SemanticsMain.makeDirs ('bin/semantics/makeDirs')
Running external method SemanticsMain.deleteTmpData ('bin/semantics/deleteTmpData')
Running external method SemanticsMain.setCommonParams ('bin/semantics/setCommonParams')
Running external method SemanticsMain.copyXMLData ('bin/semantics/copyXMLData')
Running external method SemanticsMain.genInputMaps ('bin/semantics/genInputMaps')
OOV rate per symbol:
===================:
    S1: 4.86%
    S2: 4.92%
    S3: 0.00%
Running external method SemanticsMain.genInputs ('bin/semantics/genInputs')
Running external method SemanticsMain.genHiddenObservation ('bin/semantics/genHiddenObservation')
Running external method SemanticsMain.genEndOfUtteranceObservation ('bin/semantics/genEndOfUtteranceObservation')
Running external method SemanticsMain.initSemanticModel ('bin/semantics/initSemanticModel')
Running external method SemanticsMain.initLexicalModel ('bin/semantics/initLexicalModel')
Running external method SemanticsMain.triangulate ('bin/semantics/triangulate')
Running external method SemanticsMain.trainModel ('bin/semantics/trainModel')
SemanticsMain.trainModel: <built-in>:0: fatal error: when writing output to : Přerušena roura (SIGPIPE)
SemanticsMain.trainModel: compilation terminated.
SemanticsMain.trainModel: WARNING: Can't close pipe 'cpp build/2008-06-17-15.04/gen/tri/semantics_trn.str.tri'.
Running external method SemanticsMain.forcealignTrn ('bin/semantics/forcealignTrn')
SemanticsMain.forcealignTrn: <built-in>:0: fatal error: when writing output to : Přerušena roura (SIGPIPE)
SemanticsMain.forcealignTrn: compilation terminated.
SemanticsMain.forcealignTrn: WARNING: Can't close pipe 'cpp build/2008-06-17-15.04/gen/tri/semantics_fa_trn.str.tri'.
Results:
========
    Concept Accuracy          : 100.00
    Concept Correctness       : 100.00
    Utterance Correctness     : 100.00
Running external method SemanticsMain.smoothModel ('bin/semantics/smoothModel')
SemanticsMain.smoothModel: <built-in>:0: fatal error: when writing output to : Přerušena roura (SIGPIPE)
SemanticsMain.smoothModel: compilation terminated.
SemanticsMain.smoothModel: WARNING: Can't close pipe 'cpp build/2008-06-17-15.04/gen/tri/semantics_smth.str.tri'.
Running external method SemanticsMain.scaleModel ('bin/semantics/scaleModel')
Running external method SemanticsMain.decodeHldt ('bin/semantics/decodeHldt')
SemanticsMain.decodeHldt: <built-in>:0: fatal error: when writing output to : Přerušena roura (SIGPIPE)
SemanticsMain.decodeHldt: compilation terminated.
SemanticsMain.decodeHldt: WARNING: Can't close pipe 'cpp build/2008-06-17-15.04/gen/tri/semantics_dcd.str.tri'.
Results:
========
    Concept Accuracy          :  43.84
    Concept Correctness       :  53.42
    Utterance Correctness     :  56.10
Running external method SemanticsMain.decodeTst ('bin/semantics/decodeTst')
SemanticsMain.decodeTst: <built-in>:0: fatal error: when writing output to : Přerušena roura (SIGPIPE)
SemanticsMain.decodeTst: compilation terminated.
SemanticsMain.decodeTst: WARNING: Can't close pipe 'cpp build/2008-06-17-15.04/gen/tri/semantics_dcd.str.tri'.
Results:
========
    Concept Accuracy          :  36.22
    Concept Correctness       :  49.49
    Utterance Correctness     :  44.74
Generating output XMLs for: fa_trn
Generating output XMLs for: dcd_hldt
Generating output XMLs for: dcd_tst
Running external method SemanticsMain.moveResults ('bin/semantics/moveResults 0')
SemanticsMain.moveResults: Copying files from build/2008-06-17-15.04 into results/2008-06-17-15.04
SemanticsMain.moveResults: Deleting build/2008-06-17-15.04
Út čen 17 15:15:22 CEST 2008
```

**In the directory `~/extended-HVS-parser/semantics-4/results`, there are all final results.** The archive of this directory is available [here](http://extended-hidden-vector-state-parser.googlecode.com/files/sample-run.zip).

Performance of the results (from our papers):
  * SAcc = Utterance Correctness
  * CAcc = cAcc = Concept Accuracy

### Error 1 ###

If you see:

```
Traceback (most recent call last):
  File "./semantics.py", line 6, in ?
    from svc.utils import cartezian as _cartezianProduct, strnumber, strcomma
ImportError: No module named svc.utils
```

than you have to add into you .bashrc file or you have to modify external variable:
`export PYTHONPATH=$PYTHONPATH:~/extended-HVS-parser`

### Error 2 ###

If you see:

```
SemanticsMain.copyXMLData: Traceback (most recent call last):
SemanticsMain.copyXMLData:   File "/home/filip/extended-HVS-parser/semantics-4/src/copyXML2DataRaw.py", line 270, in ?
SemanticsMain.copyXMLData:     trainList, heldoutList, testList = loadLists(dirIn)
SemanticsMain.copyXMLData:   File "/home/filip/extended-HVS-parser/semantics-4/src/copyXML2DataRaw.py", line 149, in loadLists
SemanticsMain.copyXMLData:     trainList = readXMLsAppendDate(dirIn + "/.train.list")
SemanticsMain.copyXMLData:   File "/home/filip/extended-HVS-parser/semantics-4/src/copyXML2DataRaw.py", line 92, in readXMLsAppendDate
SemanticsMain.copyXMLData:     ff = open(fName, "r")
SemanticsMain.copyXMLData: IOError: [Errno 2] No such file or directory: 'data_xml/.train.list'
Script SemanticsMain: ExternalError: External method copyXMLData ('bin/semantics/copyXMLData') returned with nonzero exit status (1)
```

than you are missing the input XML data in the directory DATA\_DIR. Original setting is `example-data` which results into `~/extended-HVS-parser/example-data`. The directory DATA\_DIR is possible to set in the file [settings.path](settingsPath.md).

### Error 3 ###

If you see:

```
SemanticsMain.triangulate: bin/semantics/triangulate: line 4: gmtkTriangulate: command not found
SemanticsMain.triangulate: bin/semantics/triangulate: line 10: gmtkTriangulate: command not found
Script SemanticsMain: ExternalError: External method triangulate ('bin/semantics/triangulate') returned with nonzero exit status (127)
```

than the scripts cannot access the GMTK binary files. Add path to the GMTK binary files into the PATH variable:
```
export PATH=$PATH:$HOME/..your-path-to-GMTK../gmtk/bin
```

For example:
```
export PATH=$PATH:$HOME/bin-speech/gmtk/bin
```

### Error 4 ###

If you see:

```
SemanticsMain.forcealignTrn: bin/semantics/forcealignTrn: line 37: cdc-treedist.py: command not found
Script SemanticsMain: ExternalError: External method forcealignTrn ('bin/semantics/forcealignTrn') returned with nonzero exit status (127)

```

than the scripts cannot access the SVC scripts. Add path to the SVC package into the PATH variable:
```
export PATH=$PATH:$HOME/extended-HVS-parser/svc
```

# Special words #

## `_unseen_` ##
Preprocesing of input utterances of the test or heldout data replaces all unseen words (we have not seen them in the training data) with this _artifficial_ word.


# Special Concepts #

## `_EMPTY_` ##
A value in the hidden vector state which represents an empty stack value at given position.

## `_DUMMY_` ##
A value in the hidden vector state (concept) which represents irrelevant input words
such as _chould you_ and ir is subsequently discarded from the outpu semantics.

## `_SINK_` ##
The concept is used as an error assertion in the model. The concept is generated onto the stack any time, the hidden variables lead to inapproriate content on the stack. Later the [stack validation](StackValidation.md) will dissable this HVS trasition sequence.