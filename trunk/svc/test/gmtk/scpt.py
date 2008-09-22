from svc.ui.gmtk import *
w = Workspace()
w.readFromFile(Collection, 'concept1GivenC2C3C4.cllctn')
w.readFromFile(DT, 'concept1GivenC2C3C4.dt')
w.readFromFile(DPMF, 'concept1GivenC2C3C4.dpmfs')
w.readFromFile(SPMF, 'concept1GivenC2C3C4.spmfs')
w.readFromFile(SCPT, 'concept1GivenC2C3C4.scpt')

t = w[SCPT, 'concept1GivenC2C3C4']
