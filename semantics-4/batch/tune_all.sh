#!/bin/bash

for d in w wp l lp wl wlp p
do
	EXPERIMENT_NAME="scale-$d" pbs/run ./semantics.py runbatch batch/tune_scale.py -vvvv --cfgfile etc/$d --debug $*
done
