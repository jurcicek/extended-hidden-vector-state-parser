The default setting for paths in the project.

# Paths #

```
#!/bin/bash

export PATH=$PATH:`pwd`/bin/

export EXPERIMENT_NAME=`date +%Y-%m-%d-%H.%M`${EXPERIMENT_NAME:+-$EXPERIMENT_NAME}

export BUILD_DIR=${REUSE_BUILD_DIR:-${BUILD_DIR:-build}/$EXPERIMENT_NAME}
export RESULT_DIR=${RESULT_DIR:-results}/${BUILD_DIR##*/}
export DATA_DIR=`pwd`/../example-data
export ANNOTATED_DIR=data_annotated
export SRC_DIR=`pwd`/src
export MAP_DIR=$BUILD_DIR/maps
export MAP_TXT_DIR=$BUILD_DIR/maps-txt
export GEN_DIR=$BUILD_DIR/gen

export PARAMS=params
export STR_DIR=params/str
export MSTR_TRN_DIR=params/mstr/trn
export MSTR_FA_TRN_DIR=params/mstr/fa_trn
export MSTR_FALIGNER_FA_TRN_DIR=params/mstr/faligner_fa_trn
export MSTR_FA_HLDT_DIR=params/mstr/fa_hldt
export MSTR_FA_TST_DIR=params/mstr/fa_tst
export MSTR_SMTH_DIR=params/mstr/smth
export MSTR_DCD_DIR=params/mstr/dcd

export DATA_XML_TRN=$BUILD_DIR/data-xml/trn
export DATA_XML_HLDT=$BUILD_DIR/data-xml/hldt
export DATA_XML_TST=$BUILD_DIR/data-xml/tst

export DATA_TRN=$BUILD_DIR/data/trn
export DATA_HLDT=$BUILD_DIR/data/hldt
export DATA_TST=$BUILD_DIR/data/tst

export DATA_TXT_TRN=$BUILD_DIR/data-txt/trn
export DATA_TXT_HLDT=$BUILD_DIR/data-txt/hldt
export DATA_TXT_TST=$BUILD_DIR/data-txt/tst

export DCD_HLDT=$BUILD_DIR/dcd/hldt
export DCD_TST=$BUILD_DIR/dcd/tst

export FA_TRN=$BUILD_DIR/fa/trn
export FA_HLDT=$BUILD_DIR/fa/hldt
export FA_TST=$BUILD_DIR/fa/tst

export GEN_DATA_CONSTANTS=$BUILD_DIR/include/dataConstants.h
export GEN_COMMON_PARAMS_SETTINGS=$BUILD_DIR/include/commonParamsSettings.h

export CONCEPT_MAP=$MAP_DIR/concept.map
export CONCEPT_MAP_TXT=$MAP_TXT_DIR/concept.map

export S1_MAP=$MAP_DIR/s1.map
export S1_MAP_TXT=$MAP_TXT_DIR/s1.map

export S2_MAP=$MAP_DIR/s2.map
export S2_MAP_TXT=$MAP_TXT_DIR/s2.map

export S3_MAP=$MAP_DIR/s3.map
export S3_MAP_TXT=$MAP_TXT_DIR/s3.map

export CPP_OPTIONS="-I $BUILD_DIR/include -I $PARAMS"

export PDT20_TOOLS=/opt/PDT-2.0/tools/machine-annotation
export PDT_WORK_DIR=$BUILD_DIR/pdt

export FSM_DIR=$BUILD_DIR/fsm

export CONFUSE_DIR=`pwd`/../confusion
export CONFUSE_DATA_DIR=$BUILD_DIR/data-confused

```