import sys
from IPython.Shell import IPythonShellEmbed 
from textwrap import wrap
sys.argv = argv
ipshell = IPythonShellEmbed() 
cmds = '\n'.join(wrap(
    ', '.join(n for n in sorted(smntcs.__class__.__dict__)
                if not n.startswith('_')
    )
))
header = \
'''============================
Semantics v.4 Embedded Shell
============================

Available commands:
-------------------
%s''' % cmds
ipshell(header=header, local_ns=globals(), global_ns=globals())
