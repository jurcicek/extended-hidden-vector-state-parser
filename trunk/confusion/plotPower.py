#!//usr/bin/python2.4
# -*-  coding: UTF-8 -*-

import sys
import struct
from pylab import *
from clnum import *

import codecs
import re


power = mpf(10.0)

##############################################################
##############################################################

def upGraph1():
    values = []
    pw = []
    for i in arange(0.2, 9.0, 0.1):
        values.append(i)
        pw.append(mpf(i))
        
    mtop = mpf(max(values))
    sum = mpf(0.0)
    for i in range(len(pw)):
#	print power
#	print mtop
#	print pw[i]
	
        pw[i] = pow(power, pow(power, (mtop - pw[i])))
#	print pw[i]
        sum += pw[i]
    
    for i in range(len(pw)):
        pw[i] = pw[i]/sum
    
    return values, pw
    
##############################################################
##############################################################

def upGraph2():
    values = []
    pw = []
    for i in arange(0.2, 9.0, 0.1):
        values.append(i)
        pw.append(i)
        
    mtop = max(values)
    sum = 0.0
    for i in range(len(pw)):
        pw[i] = pow(power, pow(power, 0.0))
        sum += pw[i]
    
    for i in range(len(pw)):
        pw[i] = pw[i]/sum
    
    return values, pw
   
##############################################################
##############################################################

fig = figure()

title("Power the measure")

xlabel('probability')
ylabel('values')

values, pw1 = upGraph1()
#values, pw2 = upGraph2()

plot(values, pw1, "g-")
#plot(values, pw2, "r-")

legend(("power1","power2"), loc = "upper center")

grid(True)
show()

