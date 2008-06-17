#ifndef COMMON_PARAMS_SETTINGS
#define COMMON_PARAMS_SETTINGS

#define SKIP_DUMMY_PROBS    0.3 0.7
#define JUMP_PROBS	        0.5 0.5 0.0 0.0 0.0 0.0 0.0

#define S1_INDEX            0
#define S2_INDEX            1
#define S3_INDEX            2

#define USE_S1              1  
#define USE_S2              1
#define USE_S3              0

#define BACKOFF_FA_PROBS	0.9999 0.0001

#define BUILD_DIR           results/2008-06-17-14.26
#define DATA_DIR            /home/honza/Research/Semantics/extended-hidden-vector-state-parser-my/semantics-4/../example-data
#define SRC_DIR             /home/honza/Research/Semantics/extended-hidden-vector-state-parser-my/semantics-4/src
#define MAP_DIR             results/2008-06-17-14.26/maps
#define MAP_TXT_DIR         results/2008-06-17-14.26/maps-txt
#define GEN_DIR             results/2008-06-17-14.26/gen
                          
#define PARAMS              params
#define STR_DIR             params/str
#define MSTR_TRN_DIR        params/mstr/trn
#define MSTR_FA_TRN_DIR     params/mstr/fa_trn
                          
#define DATA_XML_TRN        results/2008-06-17-14.26/data-xml/trn
#define DATA_XML_HLDT       results/2008-06-17-14.26/data-xml/hldt
#define DATA_XML_TST        results/2008-06-17-14.26/data-xml/tst
                          
#define DATA_TRN            results/2008-06-17-14.26/data/trn
#define DATA_HLDT           results/2008-06-17-14.26/data/hldt
#define DATA_TST            results/2008-06-17-14.26/data/tst
                          
#define DATA_TXT_TRN        results/2008-06-17-14.26/data-txt/trn
#define DATA_TXT_HLDT       results/2008-06-17-14.26/data-txt/hldt
#define DATA_TXT_TST        results/2008-06-17-14.26/data-txt/tst
                          
#define DCD_HLDT            results/2008-06-17-14.26/dcd/hldt
#define DCD_TST             results/2008-06-17-14.26/dcd/tst
                          
#define FA_TRN              results/2008-06-17-14.26/fa/trn
#define FA_HLDT             results/2008-06-17-14.26/fa/hldt
#define FA_TST              results/2008-06-17-14.26/fa/tst

#define GEN_DATA_CONSTANTS  results/2008-06-17-14.26/include/dataConstants.h

#endif
