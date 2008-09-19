# -*-  coding: utf-8  -*-
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

from svc.scripting import *
import tempfile
import codecs
import clnum
import subprocess
from svc.template import ExTemplate
import shutil
from svc.retrans import RuleList


CONFUSION_TABLE = """\
  883 	     # 	     % 	     & 	     @ 	     A 	     C 	     D 	     E 	     I 	     M 	     N 	     O 	     Q 	     R 	     S 	     T 	     U 	     Z 	     ^ 	     a 	     b 	     c 	     d 	     e 	     f 	     g 	     h 	     i 	     j 	     k 	     l 	     m 	     n 	     o 	     p 	     q 	     r 	     s 	     t 	     u 	     v 	     x 	     z 	     ~ 	     _ 	       	 
    # 	  2517 	     4 	     0 	     0 	     6 	     5 	     6 	    10 	    58 	     1 	     3 	     0 	     0 	     0 	     4 	    11 	    12 	     6 	     4 	   127 	     6 	    31 	    21 	    89 	    31 	    16 	     9 	   128 	    23 	   108 	    24 	    58 	    73 	    70 	   151 	     2 	    28 	   178 	   235 	    62 	    21 	    30 	    23 	     2 	     0 	   394 	 
    % 	     0 	   313 	     0 	     3 	     4 	     0 	     0 	     0 	     2 	     0 	     0 	     2 	     0 	     0 	     0 	     0 	    23 	     0 	     2 	    16 	     0 	     0 	     0 	     4 	     0 	     0 	     2 	     4 	     0 	     0 	    21 	     3 	     0 	   111 	     0 	     0 	     4 	     0 	     1 	    56 	     9 	     0 	     0 	     0 	     0 	    39 	 
    & 	     0 	     4 	    16 	     2 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     2 	     0 	     0 	     0 	    10 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     1 	     0 	     0 	     1 	     0 	     0 	     0 	     0 	     0 	     2 	 
    @ 	     0 	     2 	     2 	    26 	     2 	     2 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     7 	     1 	     0 	     0 	     2 	     0 	     0 	     0 	     0 	     0 	     2 	     0 	     1 	     0 	     9 	     0 	     0 	     0 	     0 	     0 	     2 	     2 	     0 	     0 	     0 	     0 	     3 	 
    A 	     0 	     2 	     0 	     2 	  1272 	     1 	     0 	     8 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     1 	     1 	     0 	   342 	     0 	     1 	     0 	    24 	     0 	     0 	     3 	     0 	     0 	     2 	    52 	     0 	     8 	     9 	     0 	     0 	    33 	     0 	     0 	     0 	     2 	     1 	     1 	     0 	     0 	    91 	 
    C 	     0 	     0 	     0 	     0 	     0 	   593 	     0 	     0 	     3 	     0 	     0 	     0 	     4 	     6 	    22 	    24 	     1 	     5 	    13 	     0 	     0 	     6 	     4 	     4 	     0 	     0 	     0 	     1 	     2 	     8 	     2 	     0 	     0 	     0 	     2 	     0 	     0 	     1 	    16 	     0 	     0 	     0 	     0 	     2 	     0 	    13 	 
    D 	     0 	     0 	     0 	     0 	     0 	     0 	   271 	     0 	     7 	     0 	     0 	     0 	     0 	     0 	     0 	     6 	     0 	     6 	     0 	     0 	     4 	     0 	    24 	     2 	     0 	     8 	     0 	     2 	    30 	     4 	     2 	     0 	     1 	     1 	     2 	     0 	     4 	     0 	     2 	     2 	     7 	     2 	     6 	    19 	     0 	    18 	 
    E 	     1 	     0 	     0 	     0 	    54 	     0 	     0 	   592 	     2 	     0 	     0 	     0 	     0 	     0 	     1 	     0 	     2 	     0 	     0 	    95 	     2 	     0 	     1 	   464 	     2 	     0 	     6 	    25 	    25 	     0 	     5 	     4 	     2 	    19 	     1 	     0 	    22 	     0 	     3 	     6 	     2 	     0 	     0 	     0 	     0 	    55 	 
    I 	     0 	     2 	     0 	     0 	     0 	     0 	     4 	     0 	  2097 	     0 	     0 	     0 	     0 	     4 	     0 	     0 	     0 	     4 	     0 	     0 	     0 	     5 	     2 	    64 	     3 	     2 	     2 	   444 	    79 	     1 	     1 	     6 	     7 	     3 	     1 	     0 	     2 	     1 	     0 	     9 	     9 	     7 	     1 	    40 	     0 	   136 	 
    M 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	    12 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     2 	     6 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	 
    N 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     7 	     0 	    64 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     2 	     0 	     0 	     0 	     1 	     0 	     0 	     1 	    18 	    17 	     0 	     0 	     0 	     0 	     0 	     0 	     4 	     0 	     0 	     0 	    23 	     0 	     6 	 
    O 	     0 	    10 	     0 	     0 	     8 	     0 	     0 	     0 	     0 	     0 	     0 	    17 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	    12 	     0 	     0 	     0 	     7 	     0 	     0 	     1 	     6 	     0 	     0 	    17 	     0 	     3 	   103 	     0 	     0 	     3 	     0 	     0 	     6 	     1 	     0 	     0 	     0 	     0 	    25 	 
    Q 	     0 	     0 	     0 	     0 	     0 	     6 	     4 	     0 	     4 	     0 	     0 	     0 	     4 	     0 	     2 	     3 	     0 	     4 	     0 	     0 	     0 	     0 	     5 	     0 	     0 	     2 	     0 	     7 	     0 	     0 	     0 	     0 	     0 	     0 	     1 	     0 	     0 	     1 	     0 	     0 	     2 	     0 	     0 	     0 	     0 	     8 	 
    R 	     0 	     0 	     0 	     0 	     0 	     6 	     2 	     0 	     2 	     0 	     0 	     0 	     0 	   295 	     6 	     0 	     0 	    14 	     4 	     1 	     0 	     3 	    16 	     5 	     0 	     0 	     4 	     1 	     1 	     2 	     0 	     2 	     2 	     0 	     0 	     0 	    30 	     6 	     2 	     0 	     6 	     0 	    10 	     2 	     0 	    10 	 
    S 	     5 	     0 	     0 	     0 	     0 	    30 	     0 	     0 	     4 	     0 	     0 	     0 	     0 	     5 	   641 	     5 	     0 	    82 	    30 	     0 	     0 	     0 	     0 	     1 	    40 	     0 	     2 	     2 	     6 	     0 	     0 	     0 	     0 	     0 	     2 	     0 	     2 	    27 	     1 	     0 	     0 	    31 	     0 	     0 	     0 	    43 	 
    T 	     0 	     0 	     0 	     0 	     0 	    17 	    21 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	   421 	     0 	     2 	     2 	     2 	     2 	     9 	    10 	     4 	     0 	     0 	     2 	     7 	    14 	    42 	     2 	     0 	     1 	     2 	     2 	     0 	     0 	     4 	    54 	     0 	     2 	     4 	     2 	     9 	     0 	    14 	 
    U 	     0 	    27 	     0 	     0 	     0 	     0 	     0 	     0 	     8 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	   231 	     0 	     0 	     0 	     0 	     2 	     1 	     9 	     0 	     0 	     4 	     4 	     0 	     0 	     2 	     7 	     2 	    38 	     2 	     0 	     4 	     0 	     0 	   235 	     3 	     0 	     2 	     0 	     0 	    22 	 
    Z 	     0 	     0 	     0 	     0 	     0 	     4 	     0 	     0 	    11 	     0 	     0 	     0 	     0 	     9 	     6 	     0 	     0 	   438 	     6 	     0 	     2 	     0 	     0 	     7 	     0 	     0 	     4 	    14 	     9 	     0 	     1 	     0 	     0 	     0 	     0 	     0 	    10 	     2 	     2 	     4 	     7 	     2 	     4 	     2 	     0 	    27 	 
    ^ 	     0 	     0 	     0 	     0 	     0 	    11 	     0 	     0 	     1 	     0 	     0 	     0 	     0 	    30 	    14 	     2 	     0 	     9 	   422 	     0 	     0 	     5 	     2 	     3 	     2 	     0 	     4 	     6 	     1 	     0 	     0 	     0 	     0 	     0 	     6 	     0 	    17 	    28 	     4 	     0 	     0 	     0 	     2 	     2 	     0 	    15 	 
    a 	     1 	     4 	     0 	     0 	   354 	     0 	     0 	    12 	     3 	     0 	     1 	     2 	     0 	     0 	     3 	     0 	     0 	     0 	     1 	  3161 	     0 	     2 	     0 	   249 	     4 	     2 	     8 	    12 	     1 	     3 	    91 	     1 	    27 	   193 	     2 	     0 	    38 	     4 	     5 	     3 	     5 	     6 	     7 	     0 	     0 	   148 	 
    b 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     2 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     4 	  1032 	     4 	    81 	     2 	     0 	    12 	     0 	    40 	     0 	     3 	    13 	    40 	    28 	     4 	    55 	     0 	     2 	     0 	    11 	     6 	   155 	     0 	     1 	     1 	     0 	    72 	 
    c 	     0 	     0 	     0 	     0 	     1 	    15 	     0 	     1 	     3 	     0 	     0 	     0 	     0 	     4 	     0 	    34 	     0 	     4 	     8 	     9 	     0 	   792 	    12 	     2 	    12 	     0 	     0 	     6 	     2 	    20 	     0 	     7 	     2 	     4 	    25 	     2 	     4 	   116 	   249 	     1 	     4 	     7 	    33 	     1 	     0 	    55 	 
    d 	     0 	     0 	     0 	     0 	     1 	     0 	    25 	     2 	     5 	     0 	     0 	     0 	     0 	     2 	     0 	     2 	     0 	     4 	     0 	     2 	    46 	    26 	  1679 	    22 	     2 	    23 	     0 	    21 	    14 	    19 	    21 	     7 	    50 	     9 	    15 	     0 	    77 	     7 	    88 	     8 	    35 	     0 	    32 	     7 	     0 	    90 	 
    e 	    12 	     2 	     0 	     0 	    22 	     0 	     2 	   190 	    35 	     0 	     0 	     2 	     0 	     1 	     3 	     0 	     2 	     8 	     6 	   404 	     7 	     2 	    26 	  4566 	     7 	     6 	    10 	   415 	    83 	     4 	     9 	    17 	    67 	   143 	     8 	     0 	   118 	    17 	    15 	    25 	    16 	     1 	    17 	     4 	     0 	   208 	 
    f 	     3 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     1 	     0 	     0 	     0 	     0 	     0 	     9 	     2 	     1 	     0 	     1 	     2 	     2 	    10 	     2 	     2 	   316 	     2 	     8 	     0 	     4 	    14 	    11 	     2 	     6 	     6 	    29 	     2 	    14 	   290 	    18 	     3 	    22 	    23 	    15 	     0 	     0 	    37 	 
    g 	     0 	     0 	     0 	     0 	     0 	     0 	     7 	     0 	    13 	     0 	     0 	     1 	     0 	     0 	     0 	     2 	     0 	     0 	     0 	     2 	    13 	     6 	    34 	     4 	     0 	   161 	     3 	     6 	     0 	    42 	     2 	    11 	     6 	     2 	    14 	     0 	     8 	     0 	     7 	     2 	    20 	    11 	     0 	     6 	     0 	    21 	 
    h 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     2 	     4 	     0 	     0 	     0 	     0 	     2 	     0 	     0 	     0 	     0 	     2 	    21 	     0 	     0 	     1 	    17 	     2 	     2 	   517 	     7 	    11 	     2 	    42 	     4 	    18 	    15 	     4 	     0 	    29 	     3 	     0 	     5 	    24 	    12 	     8 	     2 	     0 	    37 	 
    i 	     1 	     0 	     0 	     0 	     1 	     1 	     3 	     6 	   492 	     0 	     0 	     0 	     2 	     2 	     0 	     4 	     6 	     9 	     9 	    20 	     3 	     1 	    12 	   799 	     1 	     9 	     6 	  3160 	   292 	     5 	     8 	    13 	    18 	    14 	     3 	     0 	    29 	     5 	     9 	    23 	    29 	     4 	     4 	    39 	     0 	   294 	 
    j 	     0 	     0 	     0 	     0 	     0 	     2 	     5 	     4 	    81 	     0 	     0 	     0 	     0 	     2 	     1 	     6 	     1 	    14 	     0 	     0 	     2 	     0 	    12 	    90 	     0 	    10 	    12 	   161 	  1199 	     4 	    31 	     2 	     6 	     0 	     1 	     0 	    15 	     0 	     2 	     0 	    27 	     2 	     4 	    42 	     0 	   143 	 
    k 	     0 	     0 	     0 	     1 	     2 	     4 	     0 	     0 	     4 	     0 	     1 	     0 	     0 	     2 	     2 	    18 	     2 	     4 	     2 	     6 	     2 	    17 	     6 	     7 	     3 	    44 	     2 	     1 	     0 	  2081 	     6 	     4 	     9 	     9 	    80 	     0 	     8 	     9 	    70 	     5 	     5 	    15 	     2 	     2 	     0 	    48 	 
    l 	     0 	     5 	     0 	     4 	    29 	     0 	     4 	    11 	     2 	     0 	     0 	     3 	     0 	     1 	     0 	     0 	     0 	     4 	     2 	   111 	     3 	     2 	    21 	    66 	     8 	     0 	    63 	    21 	    28 	     0 	  2027 	    19 	    50 	   294 	     4 	     0 	   113 	     8 	     6 	    37 	   116 	     2 	    34 	     6 	     0 	   238 	 
    m 	     3 	     0 	     0 	     2 	     2 	     2 	     0 	     4 	    19 	     0 	     8 	     0 	     0 	     0 	     0 	     2 	     8 	     0 	     0 	     5 	     7 	     0 	    14 	     5 	     0 	     5 	     1 	    16 	     6 	     0 	    19 	  1764 	   224 	    16 	     5 	     0 	     5 	     0 	     0 	    31 	    61 	     0 	     8 	    55 	     0 	   106 	 
    n 	     2 	     0 	     0 	     0 	     2 	     0 	     0 	     5 	    15 	     0 	    10 	     0 	     0 	     0 	     0 	     4 	     1 	     0 	     0 	    11 	     4 	     4 	    61 	    46 	     0 	     2 	    12 	    52 	    10 	     0 	    25 	   214 	  2523 	    12 	     1 	     0 	    18 	     2 	     6 	    10 	    34 	     0 	    15 	   102 	     0 	   157 	 
    o 	     2 	    49 	     0 	     1 	    29 	     0 	     0 	     7 	     4 	     2 	     0 	     0 	     1 	     0 	     0 	     0 	    13 	     0 	     1 	   390 	     2 	     2 	    12 	   161 	     2 	     0 	    49 	    28 	     1 	     3 	   194 	     6 	    21 	  4199 	     4 	     0 	    89 	     1 	     6 	   207 	    23 	     2 	     4 	     0 	     0 	   275 	 
    p 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     2 	     3 	     3 	     0 	     1 	     8 	    55 	    17 	    13 	    10 	    19 	     9 	     0 	     5 	     2 	    49 	     4 	    12 	     3 	    16 	  2001 	     0 	     3 	    22 	   161 	     5 	    21 	     0 	     6 	     0 	     0 	    49 	 
    q 	     0 	     0 	     0 	     0 	     0 	     3 	     0 	     0 	     2 	     0 	     0 	     0 	     0 	     0 	     2 	     0 	     0 	     0 	     0 	     0 	     0 	    10 	     4 	     0 	     0 	     0 	     2 	     0 	     0 	     0 	     0 	     2 	     2 	     0 	     4 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     1 	     0 	     0 	     1 	 
    r 	     0 	     0 	     0 	     2 	     6 	     0 	     2 	     4 	     3 	     0 	     0 	     1 	     0 	    17 	     1 	     1 	     2 	     6 	     2 	    93 	     0 	     2 	    60 	   219 	     2 	     0 	    27 	    27 	    23 	     4 	    85 	     3 	    46 	    79 	     2 	     0 	  1756 	     5 	     1 	    11 	    51 	     0 	    35 	     3 	     0 	   182 	 
    s 	     0 	     2 	     0 	     0 	     0 	    14 	     2 	     0 	     1 	     0 	     0 	     0 	     0 	    20 	    47 	    28 	     1 	     4 	    24 	     2 	     0 	   115 	     5 	     6 	    82 	     0 	     0 	     8 	    18 	    12 	     8 	     3 	     4 	     2 	    13 	     0 	    15 	  2554 	    71 	     2 	    25 	    45 	    79 	     1 	     0 	   164 	 
    t 	     0 	     4 	     0 	     0 	     1 	     5 	     6 	     6 	     2 	     0 	     0 	     0 	     0 	     2 	     0 	    48 	     0 	     2 	     1 	     4 	     8 	   142 	   127 	    12 	     7 	    12 	     2 	     5 	     9 	   104 	    10 	     1 	    22 	     0 	   192 	     2 	    16 	    72 	  2655 	     1 	     8 	     6 	    55 	     4 	     0 	   112 	 
    u 	     0 	    31 	     0 	     0 	     0 	     1 	     0 	     0 	     7 	     0 	     0 	     0 	     0 	     0 	     2 	     0 	   143 	     0 	     2 	    13 	     8 	     0 	     6 	    19 	     2 	     1 	     3 	    23 	     2 	     3 	    39 	    12 	     5 	   379 	     1 	     0 	    23 	     3 	     4 	  1090 	    20 	     0 	     5 	     5 	     0 	    71 	 
    v 	     0 	     5 	     0 	     0 	     0 	     0 	     0 	     3 	     2 	     0 	     0 	     0 	     0 	     2 	     1 	     2 	     7 	     0 	     0 	     2 	    52 	     6 	    35 	     7 	     4 	     8 	    33 	    26 	    46 	     1 	   134 	    75 	    72 	    32 	     9 	     0 	    81 	     6 	    18 	    26 	  1809 	     0 	    75 	     8 	     0 	   136 	 
    x 	     7 	     0 	     0 	     0 	     2 	     3 	     1 	     0 	     3 	     0 	     0 	     0 	     0 	     0 	     8 	     2 	     0 	     6 	     0 	     8 	     2 	    10 	     4 	     8 	    14 	     6 	     8 	     1 	     2 	    33 	     4 	     2 	     2 	     0 	     6 	     0 	    26 	    73 	     0 	     2 	     0 	   422 	     2 	     0 	     0 	    21 	 
    z 	     1 	     2 	     0 	     0 	     0 	     0 	     6 	     0 	    10 	     0 	     0 	     0 	     0 	     6 	     2 	     0 	     2 	    14 	     0 	     8 	    11 	    18 	    77 	    26 	    11 	     8 	    13 	    45 	     9 	     5 	    30 	    10 	    37 	    15 	     6 	     2 	    51 	    30 	    17 	    11 	   131 	    10 	   989 	     8 	     0 	   124 	 
    ~ 	     0 	     0 	     0 	     0 	     0 	     2 	    19 	     0 	    83 	     0 	     4 	     0 	     0 	     0 	     2 	     7 	     0 	     3 	     0 	     0 	     2 	     0 	     0 	    24 	     0 	    12 	     2 	    36 	    31 	     0 	     4 	    97 	    87 	     2 	     0 	     0 	     2 	     0 	     2 	     4 	    10 	     0 	     3 	  1365 	     0 	   156 	 
    _ 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	     0 	 
      	    51 	     3 	     0 	     0 	    31 	     9 	     5 	     7 	    90 	     0 	     0 	     0 	     0 	     7 	     5 	     2 	     6 	     6 	     1 	   118 	     6 	    22 	    40 	   165 	     3 	     5 	     0 	   175 	    35 	    45 	    62 	    42 	    73 	   119 	    55 	     0 	    56 	    51 	    69 	    39 	    35 	     9 	    34 	    12 	     0 	     0 	 
"""

PHONEME_TABLE = {'a':'a', u'á':'A', 'b':'b', 'c':'c', u'č':'C', 'd':'d',
        u'ď':'D', 'e':'e', u'é':'E', u'ě':'e', 'f':'f', 'g':'g', 'h':'h',
        'i':'i', u'í':'I', 'j':'j', 'k':'k', 'l':'l', 'm':'m', 'm':'M',
        'n':'n', 'n':'N', u'ň':'~', 'o':'o', u'ó':'O', u'ö':'O', 'p':'p',
        'r':'r', u'ř':'R', 's':'s', u'š':'S', 't':'t', u'ť':'T', 'u':'u',
        u'ú':'U', u'ů':'U', u'ü':'u', 'v':'v', 'w':'v', 'y':'i', u'ý':'I',
        'x':'k', 'z':'z', u'ž':'Z'}

CLEANER = RuleList.createFromString(r"""
(?m)^(.*[^!])$ : \1!
:::::::::::::
[^%s!] : \_
:::::::::::::
\_\_ : \_
!\s*! : !
:::::::::::::
! : \n
(?m)^\_ :
""" % ''.join(PHONEME_TABLE.keys()))

def _distLevenshtein(a, b, cost):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
        
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0.0]*n
        
        for j in range(1,n+1):
            insertion    = previous[j]   + 3.0
            deletion     = current[j-1]  + 3.0
            substitution = previous[j-1] + 1.2*cost(a[j-1], b[i-1])
            
            current[j] = min(insertion, deletion, substitution)
            
    return current[n]


class Confusion(PythonEgg):
    TEMP_FILES = {
        'vocab': 'vocab.txt',
        'text': 'utt.txt',
        'bigramlm': 'bigram.lm',
        'map': 'map.txt',
        'map_power': 'map_power.txt',
        'input': 'input.txt',
        'output': 'output.txt',
        'input_mlf': 'input.mlf',
        'output_mlf': 'output.mlf',
        'null': 'null',
    }

    def __init__(self):
        super(Confusion, self).__init__()
        self._delOnRelease = True

    def cleanText(self, txt):
        return CLEANER.apply(txt.lower())

    def getTempDir(self):
        if hasattr(self, '_tempDir'):
            return self._tempDir
        else:
            dir = tempfile.mkdtemp('', 'confusion')
            self._tempDir = dir
            self._delOnRelease = True
            return dir

    def tempName(self, t):
        return os.path.join(self.tempDir, self.TEMP_FILES[t])

    def vocabulary(self, txt):
        return set(txt.split())

    def writeVocabulary(self, vocab):
        fw = codecs.open(self.tempName('vocab'), 'w', 'utf-8')
        for w in sorted(vocab):
            print >> fw, w
        fw.close()

    def writeText(self, txt):
        fw = codecs.open(self.tempName('text'), 'w', 'utf-8')
        fw.write(txt)
        fw.close()

    def makeBigramLM(self):
        os.system("ngram-count -sort -order 2 -lm %s -text %s -wbdiscount" % \
                (self.tempName('bigramlm'), self.tempName('text')))

    def getConfusionTable(self):
        lines = CONFUSION_TABLE.splitlines()
        
        alph = lines[0].split()[1:-1]

        confusion = {}
        for i, a in enumerate(alph):
            confusion[a] = {}
            
            nums = lines[i+1].split()
            
            total = 0.0
            for j, b in enumerate(alph):
                confusion[a][b] = float(nums[j+1])
                total += confusion[a][b]
            
            # normalization
            for b in alph:
                confusion[a][b] = confusion[a][b]/total

        return confusion

    def vocabDist(self, word, vocab):
        top = []
        for w in vocab:
            top.append([_distLevenshtein(w, word, self.confusionCost), word, w])
    
        return top

    def confusionCost(self, a, b):
        pa_a = PHONEME_TABLE[a]
        pa_b = PHONEME_TABLE[b]
        return 1 - self._confusionTable[pa_a][pa_b]

    def applyPower(self, conf_list, power):
        mtop = clnum.mpf(max(conf_list)[0])
        s = clnum.mpf(0.0)
        for t in conf_list:
            t[0] = pow(power, pow(power, mtop - clnum.mpf(t[0])))
            s += t[0]
        
        for t in conf_list:
            t[0] = t[0]/s
            
        return conf_list


    def makeMap(self, vocab, word_n):
        map = {}

        for w in vocab:
            dist = self.vocabDist(w, vocab)
            dist = sorted(dist)[:word_n]
            
            orig = dist[0][1]
            map[orig] = {}
            for dist, orig, new in dist:
                map[orig][new] = dist

        return map

    def powerMap(self, map, word_power):
        new_map = {}

        for orig, items in map.iteritems():
            dist = []
            for new, score in items.iteritems():
                dist.append( [score, orig, new] )

            if not dist:
                continue

            dist = self.applyPower(dist, word_power)
            dist.sort(reverse=True)    
            
            orig = dist[0][1]
            new_map[orig] = {}
            for dist, orig, new in dist:
                new_map[orig][new] = dist

        return new_map

    def writeMap(self, map, type='map'):
        rev = (type == 'map_power')
        fw = codecs.open(self.tempName(type), 'w', 'utf-8')
        for orig, confusions in sorted(map.iteritems()):
            fw.write('%-15s ' % orig)
            for new, score in sorted(confusions.iteritems(), key=lambda i:i[1], reverse=rev):
                fw.write('%-15s %1.6f ' % (new, score))
            fw.write('\n')
        fw.close()

    def readMap(self, type='map'):
        map = {}
        fr = codecs.open(self.tempName(type), 'r', 'utf-8')
        for line in fr:
            items = line.split()
            orig = items[0]
            items = items[1:]
            map[orig] = {}
            for i in range(0, len(items), 2):
                new = items[i]
                score = float(items[i+1])
                map[orig][new] = score
        fr.close()
        return map

    def initialize(self, txt, word_n=None, word_power=None, logger=None):
        if word_n is None:
            word_n = 50
        if word_power is None:
            word_power = 1.1
        if logger is not None: logger.info("Cleaning text")
        txt = self.cleanText(txt)
        if logger is not None: logger.info("Making vocabulary")
        vocab = self.vocabulary(txt)
        if logger is not None: logger.info("Writing text")
        self.writeText(txt)
        self.writeVocabulary(vocab)
        if logger is not None: logger.info("Making bigram LM")
        self.makeBigramLM()
        self._confusionTable = self.getConfusionTable()
        if logger is not None: logger.info("Creating mapping")
        map = self.makeMap(vocab, word_n)
        self.writeMap(map, 'map')
        if logger is not None: logger.info("Creating power mapping")
        map = self.powerMap(map, word_power)
        self.writeMap(map, 'map_power')
        self.confuse(txt)
        return self.evaluate()

    def initializeFromFile(self, fn, word_n=None, word_power=None, encoding='utf-8', logger=None):
        fr = codecs.open(fn, 'r', encoding)
        txt = fr.read()
        fr.close()
        return self.initialize(txt, word_n, word_power, logger=logger)

    def convertTxtIntoMLF(self, in_fn, out_fn, ext):
        fr = codecs.open(in_fn, 'r', 'utf-8')
        fw = codecs.open(out_fn, 'w', 'utf-8')
        fw.write("#!MLF!#\n")
        for i, line in enumerate(fr):
            fw.write('"*/%06d.%s"\n' % (i, ext))
            for w in line.split():
                fw.write(w.strip()+'\n')
            fw.write('.\n')
        fw.close()

    def evaluate(self):
        lab_fn = self.tempName('input')
        lab_mlf = self.tempName('input_mlf')
        self.convertTxtIntoMLF(lab_fn, lab_mlf, 'lab')
        rec_fn = self.tempName('output')
        rec_mlf = self.tempName('output_mlf')
        self.convertTxtIntoMLF(rec_fn, rec_mlf, 'rec')

        fw = file(self.tempName('null'), 'w')
        fw.close()

        hresults = subprocess.Popen(['HResults', '-I', lab_mlf, '/dev/null', rec_mlf], stdout=subprocess.PIPE)
        stdout = hresults.communicate()[0]
        template = ExTemplate('WORD: %Corr=$Corr, Acc=$Acc [', 'ignore_end')
        for line in stdout.splitlines():
            ret = template.backload(line)
            if ret is not None:
                ret['Corr'] = float(ret['Corr'])
                ret['Acc'] = float(ret['Acc'])
                return ret

    def initialized(self):
        return hasattr(self, '_tempDir')

    def confuseFile(self, fn, encoding='utf-8'):
        fr = codecs.open(fn, 'r', encoding)
        txt = fr.read()
        fr.close()
        return self.confuse(txt)

    def modify(self, word_power):
        map = self.readMap('map')
        map = self.powerMap(map, word_power)
        self.writeMap(map, 'map_power')

    def confuse(self, txt):
        if not self.initialized():
            raise ValueError("Confusion not initialized")

        txt = self.cleanText(txt)

        word_lmw = 2.0
        txt_fn = self.tempName('input')
        out_fn = self.tempName('output')
        map_fn = self.tempName('map_power')
        lm_fn = self.tempName('bigramlm')

        fw = codecs.open(txt_fn, 'w', 'utf-8')
        fw.write(txt)
        fw.close()

        fw = codecs.open(out_fn, 'w', 'utf-8')

        disambig = subprocess.Popen(['disambig', '-lmw', str(word_lmw),
            '-mapw', '1', '-scale', '-keep-unk', '-text', txt_fn, '-map',
            map_fn, '-lm', lm_fn], stdout=fw)
        disambig.wait()
        fw.close()

        fr = codecs.open(out_fn, 'r', 'utf-8')
        output = fr.read()
        fr.close()

        ret = output.replace('<s> ', '').replace(' </s>', '')

        fw = codecs.open(out_fn, 'w', 'utf-8')
        fw.write(ret)
        fw.close()

        results = self.evaluate()

        return ret, results

    def release(self):
        if hasattr(self, '_tempDir'):
            if self._delOnRelease:
                shutil.rmtree(self._tempDir)
            del self._tempDir

    def __del__(self):
        self.release()

    def save(self, dir_name):
        if not self.initialized():
            raise ValueError("Confusion not initialized")
        try:
            shutil.rmtree(dir_name)
        except OSError:
            pass
        shutil.move(self.tempDir, dir_name)
        self._tempDir = dir_name
        self._delOnRelease = False

    def load(self, dir_name):
        if self.initialized():
            self.release()
        self._tempDir = dir_name
        self._delOnRelease = False


class ConfusionScript(ExScript):
    options = {
        'command': ExScript.CommandParam,
        'init.model_dir': (Required, String),
        'init.inputfn': (Required, String),
        'init.encoding': String,
        'init.power': Float,
        'init.hnum': Integer,
        'confuse.model_dir': OptionAlias,
        'confuse.inputfn': OptionAlias,
        'confuse.encoding': OptionAlias,
        'confuse.power': OptionAlias,
    }

    posOpts = ['command', 'model_dir', 'inputfn']

    def logResults(self, results):
        self.logger.info("Correctness: %.2f", results['Corr'])
        self.logger.info("Accuracy:    %.2f", results['Acc'])

    @ExScript.command
    def init(self, model_dir, inputfn, power=None, hnum=None, encoding='utf-8'):
        c = Confusion()
        results = c.initializeFromFile(inputfn, hnum, power, encoding=encoding, logger=self.logger)
        c.save(model_dir)
        self.logResults(results)
    
    @ExScript.command
    def confuse(self, model_dir, inputfn, encoding='utf-8', power=None):
        c = Confusion()
        c.load(model_dir)
        if power is not None:
            c.modify(power)
        output, results = c.confuseFile(inputfn, encoding=encoding)
        print output.encode(encoding)
        self.logResults(results)

if __name__ == '__main__':
    s = ConfusionScript()
    s.run()
