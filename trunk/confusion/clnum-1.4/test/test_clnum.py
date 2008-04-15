#-----------------------------------------------------------------------------
# Copyright (c) 2005  Raymond L. Buvel
#
# This file is part of clnum, a Python interface to the Class Library for
# Numbers.  This module tests the interface to CLN.
#
# The clnum module is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) any
# later version.
#
# The clnum nodule is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# clnum; if not, write to the Free Software Foundation, Inc., 59 Temple Place,
# Suite 330, Boston, MA  02111-1307  USA
#-----------------------------------------------------------------------------

import clnum, math, cmath
from clnum import *

#------------------------------------------------------------------------------
# NOTES:
#
# 1) The basic assumption of this test is that the CLN is reliable.  Only
# the Python interface (the clnum module) is verified.  Consequently, a number
# of tests use comparison against Python float or complex results.  Obviously,
# this is not a valid test of a high precision library.  However, it does
# adequately test the interface to the library.
#
# 2) On a 64-bit machine, the CLN library uses 2 64-bit integers for the
# default precision.  This gives a precision of 36 instead of 26 (the default
# on 32-bit platforms).  Consequently, this test needs to check against both
# values.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Verify that the correct exception is raised.

def testex(s, ex):
    err = False
    try:
        exec s
    except ex:
        err = True
    assert err

#------------------------------------------------------------------------------
a = mpf(1234567890123456789012345678901234567890123456789, 50)
s = repr(a)
assert s == "mpf('1.234567890123456789012345678901234567890123456789e48',55)"
assert str(a) == '1.234567890123456789e48'
# Verify that the representation can be converted back to the same value.
x = eval(s)
assert x == a
assert x.prec == a.prec

assert a.prec == 55
# The precision is read-only so check this.  Note Python 2.5 raises
# AttributeError while previous versions raise TypeError.
testex('a.prec = 10', (TypeError,AttributeError))

# Verify the initial default.
assert clnum.get_default_precision() in (26,36)

clnum.set_default_precision(0)
assert clnum.get_default_precision() in (26,36)

clnum.set_default_precision(50)
assert clnum.get_default_precision() == 55

clnum.set_default_precision(0)
assert clnum.get_default_precision() == 55

# This gets us back to the default.
clnum.set_default_precision(20)
assert clnum.get_default_precision() in (26,36)

# Check the constants pi and e against the math library.
assert abs(clnum.pi(0)-math.pi) < 1e-15
assert abs(clnum.exp1(0)-math.e) < 1e-15

# Verify that the precision is set correctly for conversions.
assert mpf(1).prec in (26,36)
assert mpf(1L).prec in (26,36)
assert mpf(mpq(1)).prec in (26,36)
assert mpf(1.0).prec == 17
assert mpf(mpf(1.0)).prec == 17
assert mpf(1.0,20).prec in (26,36)
assert mpf(mpf(1.0,20)).prec in (26,36)

# Can't convert a non-number
testex('mpf([])', TypeError)

# This generates a Python float with value infinity.
testex('mpf(1e1000)', ValueError)

a = mpf(2)
b = mpf(3)
assert a.prec in (26,36)

# Check basic arithmetic between mpf
assert (a+b) == 5
assert (a-b) == -1
assert (a*b) == 6
assert abs(a/b - 2.0/3) < 1e-16

# Mix with Python ints
assert (a+1) == 3
assert (a-1) == 1
assert (a*5) == 10
assert (a/4) == 0.5

# Mix with Python longs
assert (a+1L) == 3
assert (a-1L) == 1
assert (a*5L) == 10
assert (a/4L) == 0.5

# Mix with Python floats
assert (a+1.0) == 3
assert (a-1.0) == 1
assert (a*5.0) == 10
assert (a/4.0) == 0.5

# Mix with mpq
assert (a+mpq(1)) == 3
assert (a-mpq(1)) == 1
assert (a*mpq(5)) == 10
assert (a/mpq(4)) == 0.5

a = -a

assert a == -2
assert abs(a) == 2
assert +a == -2

# Variations on division.

assert mpf(5)//3 == 1
assert mpf(5)%3 == 2
q,r = divmod(mpf(5),3)
assert q == 1 and r == 2

# Powers

assert mpf(0)**0 == 1
assert mpf(2)**0 == 1
assert mpf(0)**1 == 0
assert mpf(0)**0.5 == 0
x,y = mpf(2),1/mpf(2)
assert abs(x**y - 2**0.5) < 1e-16

# The result is complex so an exception is generated.
testex('(-x)**y', ValueError)

# Bools
assert bool(mpf(1)) is True
assert bool(mpf(0)) is False

# Hash - the hash operation should match the behavior of floats.
assert hash(mpf(1)/2) == hash(0.5)
assert hash(mpf(10)) == hash(10.0)

#------------------------------------------------------------------------------
a = mpq(1234567890123456789012345678901234567890123456789,5)
s = repr(a)
assert s == 'mpq(1234567890123456789012345678901234567890123456789,5)'
assert str(a) == '1234567890123456789012345678901234567890123456789/5'
# Verify that the representation can be converted back to the same value.
assert eval(s) == a
assert mpq(str(a)) == a

a = mpq(2)
b = mpq(3)

# Check basic arithmetic between mpq
assert (a+b) == 5
assert (a-b) == -1
assert (a*b) == 6
assert str(a/b) == '2/3'

# Mix with Python ints
assert (a+1) == 3
assert (a-1) == 1
assert (a*5) == 10
assert float(a/4) == 0.5

# Mix with Python longs
assert (a+1L) == 3
assert (a-1L) == 1
assert (a*5L) == 10
assert float(a/4L) == 0.5

# Mix with Python floats.
#
# A Python float type cannot recognize an mpq and mpq refuses to convert a
# float to a rational.  Consequently, the operation fails.
testex('a+1.0', TypeError)
testex('a-1.0', TypeError)
testex('a*1.0', TypeError)
testex('a/1.0', TypeError)

# Mix with mpf
#
# In this case mpq refuses to accept an mpf so the operation is performed on
# the mpq converted to an mpf.
assert (a+mpf(1)) == 3
assert (a-mpf(1)) == 1
assert (a*mpf(5)) == 10
assert (a/mpf(4)) == 0.5
assert type(a+mpf(1)) == mpf
assert type(a-mpf(1)) == mpf
assert type(a*mpf(5)) == mpf
assert type(a/mpf(4)) == mpf

a = -a

assert a == -2
assert abs(a) == 2
assert +a == -2

# Powers

assert mpq(0)**0 == 1
assert mpq(2)**0 == 1
assert mpq(0)**1 == 0
assert mpq(0)**2 == 0
assert mpq(5)**3 == 125

# The exponent is not an integer so an exception is generated.
testex('mpq(2)**mpq(1,2)', ValueError)

# Bools
assert bool(mpq(1)) is True
assert bool(mpq(0)) is False

# Hash - the hash operation should match the behavior of floats.
assert hash(mpq(1)/2) == hash(0.5)
assert hash(mpq(10)) == hash(10.0)

x = mpq(2)/3
assert x.numer == 2
assert x.denom == 3

#------------------------------------------------------------------------------
# Verify that the precision is set correctly for conversions.
assert cmpf(1).prec in (26,36)
assert cmpf(1L).prec in (26,36)
assert cmpf(mpq(1)).prec in (26,36)
assert cmpf(1.0).prec == 17
assert cmpf(mpf(1.0)).prec == 17
assert cmpf(1.0,0,20).prec in (26,36)
assert cmpf(mpf(1.0,20)).prec in (26,36)

# Can't convert a non-number
testex('cmpf([])', TypeError)

# This generates a Python float with value infinity.
testex('cmpf(1,1e1000)', ValueError)
testex('cmpf(1e1000,1)', ValueError)

a = cmpf(2)
b = cmpf('3j')

assert a.prec in (26,36)
assert b.prec in (26,36)
assert cmpf(3j).prec == 17

assert a.real == 2
assert a.imag == 0

assert b.real == 0
assert b.imag == 3

# Check basic arithmetic between cmpf
assert (a+b) == 2+3j
assert (a-b) == 2-3j
assert (a*b) == 6j
assert abs(a/b - 2.0/3j) < 1e-16

# Mix with Python ints
assert (a+1) == 3
assert (a-1) == 1
assert (a*5) == 10
assert (a/4) == 0.5

# Mix with Python longs
assert (a+1L) == 3
assert (a-1L) == 1
assert (a*5L) == 10
assert (a/4L) == 0.5

# Mix with Python floats
assert (a+1.0) == 3
assert (a-1.0) == 1
assert (a*5.0) == 10
assert (a/4.0) == 0.5

# Mix with mpq
assert (a+mpq(1)) == 3
assert (a-mpq(1)) == 1
assert (a*mpq(5)) == 10
assert (a/mpq(4)) == 0.5

a = -a

assert a == -2
assert abs(a) == 2
assert +a == -2

# Powers

assert cmpf(0)**0 == 1
assert cmpf(2)**0 == 1
assert cmpf(0)**1 == 0
assert cmpf(0)**0.5 == 0
assert cmpf(-1)**mpq(1,2) == 1j
x,y = cmpf(2),1/cmpf(2)
assert abs(x**y - 2**0.5) < 1e-16

# Unlike the mpf case, this should give a complex result and not throw an
# exception.
abs((-x)**y - (2**0.5)*1j) < 1e-16

# Bools
assert bool(cmpf(1)) is True
assert bool(cmpf(0)) is False

# Hash - the hash operation should match the behavior of complex.
assert hash(cmpf(1,3)/2) == hash(complex(1,3)/2)
assert hash(cmpf(10)) == hash(complex(10))

#------------------------------------------------------------------------------
# Library functions.  Compare the results to the Python math and cmath
# libraries just to make sure the functions are mapped correctly.  The python
# libraries are not up to the test of accuracy.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Trig functions - real version

# Pick a value that gives distinctly different results for sin, cos , and tan.
x = math.pi/6

assert abs(sin(x) - math.sin(x)) < 1e-14
assert abs(cos(x) - math.cos(x)) < 1e-14
assert abs(tan(x) - math.tan(x)) < 1e-14

assert abs(asin(sin(x)) - x) < 1e-14
assert abs(acos(cos(x)) - x) < 1e-14
assert abs(atan(tan(x)) - x) < 1e-14

assert abs(degrees(x) - 30) < 1e-14
assert abs(radians(30) - x) < 1e-14
assert abs(pi() - math.pi) < 1e-14

assert abs(atan2(sqrt(mpq(3,4)),mpq(1,2)) - radians(60)) < 1e-20
assert abs(atan2(sqrt(mpq(3,4)),-mpq(1,2)) - radians(120)) < 1e-20
assert abs(atan2(-sqrt(mpq(3,4)),mpq(1,2)) - radians(-60)) < 1e-20

#------------------------------------------------------------------------------
# Trig functions - complex version

# Pick a value that gives distinctly different results for sin, cos , and tan.
x = 1j*math.pi/6

assert abs(sin(x) - cmath.sin(x)) < 1e-14
assert abs(cos(x) - cmath.cos(x)) < 1e-14
assert abs(tan(x) - cmath.tan(x)) < 1e-14

assert abs(asin(sin(x)) - x) < 1e-14
assert abs(acos(cos(x)) - x) < 1e-14
assert abs(atan(tan(x)) - x) < 1e-14

assert abs(cis(x) - (cos(x)+1j*sin(x))) < 1e-14

#------------------------------------------------------------------------------
# Exponential and log functions - real version

x = 0.5

assert abs(sqrt(x) - math.sqrt(x)) < 1e-14

assert abs(log(x) - math.log(x)) < 1e-14
assert abs(log10(x) - math.log10(x)) < 1e-14
assert abs(log(32,2) - 5) < 1e-14

assert abs(exp1() - math.e) < 1e-14
assert abs(exp(x) - math.exp(x)) < 1e-14
assert abs(exp(log(x)) - x) < 1e-14

#------------------------------------------------------------------------------
# Exponential and log functions - complex version

x = complex(-1)

assert abs(sqrt(x) - cmath.sqrt(x)) < 1e-14

x = complex(0,0.5)

assert abs(log(x) - cmath.log(x)) < 1e-14
assert abs(log10(x) - cmath.log10(x)) < 1e-14
assert abs(log(x,2) - cmath.log(x)/cmath.log(2)) < 1e-14

assert abs(exp(x) - cmath.exp(x)) < 1e-14
assert abs(exp(log(x)) - x) < 1e-14

#------------------------------------------------------------------------------
# Hyperbolic functions - real version

x = 0.5

assert abs(cosh(x) - math.cosh(x)) < 1e-14
assert abs(sinh(x) - math.sinh(x)) < 1e-14
assert abs(tanh(x) - math.tanh(x)) < 1e-14

#------------------------------------------------------------------------------
# Hyperbolic functions - complex version

x = 0.5j

assert abs(cosh(x) - cmath.cosh(x)) < 1e-14
assert abs(sinh(x) - cmath.sinh(x)) < 1e-14
assert abs(tanh(x) - cmath.tanh(x)) < 1e-14

assert abs(acosh(x) - cmath.acosh(x)) < 1e-14
assert abs(asinh(x) - cmath.asinh(x)) < 1e-14
assert abs(atanh(x) - cmath.atanh(x)) < 1e-14

#------------------------------------------------------------------------------
# Rounding operations.

assert type(round(0.5)) is mpf
assert type(round(mpq(1,2))) is mpf
assert type(floor(0.5)) is mpf
assert type(ceil(0.5)) is mpf

assert round(0.5) == 1
assert round(-0.5) == -1
assert round(1.5) == 2
assert round(-1.5) == -2
assert abs(round(0.25,1) - 0.3) < 1e-14
assert abs(round(1.123456789,4) - 1.1235) < 1e-14

assert ceil(0.5) == 1
assert ceil(-0.5) == 0
assert ceil(1.1) == 2
assert ceil(-1.1) == -1

assert floor(0.5) == 0
assert floor(-0.5) == -1
assert floor(1.1) == 1
assert floor(-1.1) == -2

#------------------------------------------------------------------------------
# Misc functions.

assert abs(hypot(1,2) - math.hypot(1,2)) < 1e-14
assert abs(hypot(-2,1) - math.hypot(1,2)) < 1e-14
assert abs(hypot(-2,-1) - math.hypot(1,2)) < 1e-14
assert abs(hypot(2,-1) - math.hypot(1,2)) < 1e-14
assert abs(hypot(1,2) - sqrt(5)) < 1e-20

assert hypot(0.0,0) == 0
assert hypot(0.0,0).prec == 17
assert hypot(0,0).prec in (26,36)

#------------------------------------------------------------------------------
# Type checking functions.

assert isexact(1)
assert isexact(1L)
assert isexact(mpq(1,2))
assert isexact(cmpq(1,2))
assert not isexact(1.0)
assert not isexact(1+1j)
assert not isexact(mpf(1))
assert not isexact(cmpf(1))

assert isreal(1)
assert isreal(1L)
assert isreal(1.0)
assert isreal(mpq(1,2))
assert isreal(mpf(1))
assert not isreal(1+1j)
assert not isreal(cmpq(1,2))
assert not isreal(cmpf(1))

assert not iscomplex(1)
assert not iscomplex(1L)
assert not iscomplex(1.0)
assert not iscomplex(mpq(1,2))
assert not iscomplex(mpf(1))
assert iscomplex(1+1j)
assert iscomplex(cmpq(1,2))
assert iscomplex(cmpf(1))

#------------------------------------------------------------------------------
# Test the combinatorial functions.

assert factorial(10) == 3628800
assert doublefactorial(9) == 945
assert doublefactorial(10) == 3840
assert [binomial(4,i) for i in range(5)] == [1,4,6,4,1]

#------------------------------------------------------------------------------
# Rational approximation function.

assert ratapx(pi()) == mpq(355,113)
assert ratapx(-pi()) == mpq(-355,113)
assert ratapx(sqrt(2)) == mpq(19601,13860)
assert ratapx(0) == 0
assert ratapx(1) == 1
assert ratapx(-1) == -1
assert ratapx(1/pi()) == mpq(113,355)

#------------------------------------------------------------------------------
# Root finder.

def f(x): return x*x - 2

assert abs(find_root(f,1,2,1e-20) - sqrt(2)) < 1e-20

# TWBRF test function.

def f(x): return 4*sin(x)+exp(-x/6)

x = find_root(f, 0, 6, 1e-20)
assert abs(f(x)) < 1e-20

#------------------------------------------------------------------------------
# Bug fixes.  This section is for test cases that verify fixes for bugs that
# were found.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# The error in the following case was that the real part had default precision
# of 26 and the imaginary part had double precision of 17.  Now for mixed
# precision, the higher precision number is degraded to the lower precision.
z = cmpf(1,1.0)
assert z.prec == 17 and z.real.prec == 17 and z.imag.prec == 17

#------------------------------------------------------------------------------
# The following calculations produced a precision of 5 due to some issue with
# the default conversion in CLN.
assert (10**mpf(2)).prec in (26,36)
assert (cmpq('1/2+0j')**cmpf(2)).prec in (26,36)
assert (2**cmpf(2)).prec in (26,36)

#------------------------------------------------------------------------------
# The conversion between Python longs and CLN integers was very inefficient for
# large values (greater than 100000 decimal digits).  These test cases are to
# verify that the functions are not broken.
#
# Use a test value that has no long runs of identical digits and covers about
# 2.5 of the blocks used in the conversion routine.  This covers all of the
# execution paths in the code.

a = 7 ** 13678
b = mpq(7) ** 13678
assert mpq(a) == b  # Tests long to CLN integer.
assert b.numer == a # Tests CLN integer to long.

#------------------------------------------------------------------------------
# When an exact zero was used in multiply and divide of mpf and cmpf values,
# the CLN library returns an exact zero which was getting converted to float
# using default precision.  These test cases verify that the anomaly is fixed.

for v in [mpf(1,30), mpf(1,50)]:
    for z in (0, 0L, mpq(0)):
        assert (v*z).prec == v.prec
        assert (z*v).prec == v.prec
        assert (z/v).prec == v.prec
        assert (z%v).prec == v.prec
        assert (z//v).prec == v.prec
        assert divmod(z,v)[0].prec == v.prec
        assert divmod(z,v)[1].prec == v.prec

    # Verify that floating point values are not treated the same as exact
    # values.
    z = 0.0
    assert (v*z).prec == 17
    assert (z*v).prec == 17
    assert (z/v).prec == 17
    assert (z%v).prec == 17
    assert (z//v).prec == 17
    assert divmod(z,v)[0].prec == 17
    assert divmod(z,v)[1].prec == 17

for v in [cmpf(1,prec=30), cmpf(1,prec=50)]:
    for z in (0, 0L, mpq(0), cmpq(0)):
        assert (v*z).prec == v.prec
        assert (z*v).prec == v.prec
        assert (z/v).prec == v.prec

    # Verify that floating point values are not treated the same as exact
    # values.
    for z in (0.0, 0j):
        assert (v*z).prec == 17
        assert (z*v).prec == 17
        assert (z/v).prec == 17

#------------------------------------------------------------------------------
print 'All Tests PASS'
