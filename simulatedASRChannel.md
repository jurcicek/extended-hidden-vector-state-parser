This chapter describe how to use simulated ASR channel on the input of the parser.


# Usage of simmulated ASR channel in semantics-4 #

First of all, you have to have instaleded PDT-2.0 with the script `run_tagger`
(which altered 'run\_all' so that it performes only the mophological analysis and tagging). Then you need `confusion` package from the top directory of the parser. This package performs the mentioned "confusion" of the input word sequences.

You must set the follwing variables in the [settings.path](settingsPath.md):
```
export PDT20_TOOLS=/opt/PDT-2.0/tools/machine-annotation
export CONFUSE_DIR=`pwd`/../confusion
```

To set the confusion on, you have to set the variable CONFUSE to 1
```
CONFUSE = 1
```
in the file `etc/confused`.

After setting the simulated channel on, zou must to decide what data sets will be used on each inputs (input features).

For training you can chose from:
  * `S[123]_DATASET`

For heldout and testing data, you can chose from:
  * `S[123]_DATASET_DCD` (if it is not set, use `S[123]_DATASET`)

Availabe confusion sets:
  * Words: word, conf\_word
  * Lemmas: lemma, conf\_lemma
  * POS tags: pos, conf\_pos

After approriet modification of etc/confused, you shuld be able to run `semantics.py` with necessary paremeters.

It necessary to used not only parameters from [settings.path](settingsPath.md) but also `etc/confused`. It can be done by:
```
./settings.py -vvv all --cfgfile etc/confused
```