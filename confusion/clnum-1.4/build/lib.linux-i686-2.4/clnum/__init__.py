#-----------------------------------------------------------------------------
# Copyright (c) 2006  Raymond L. Buvel
#
# This file is part of clnum, a Python interface to the Class Library for
# Numbers.  This module provides module initialization and some functions coded
# in Python instead of C++.
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
from clnum import *
__doc__ = clnum.__doc__

_version = '1.4'

def ratapx(x, maxint=0x7FFF):
    '''Return the input value x approximated as a rational number where the
    numerator and denominator are both less than or equal to maxint.
    '''
    x = mpq(x)
    u = x.numer
    v = x.denom

    f = False # Indicates the fraction is not flipped

    if maxint <= 1:
        raise ValueError('maxint must be greater than 1')

    sign = 1
    if u < 0:
        u = -u
        sign = -1

    if u == v:
        return mpq(sign*1)

    if u == 0:
        return mpq(0)

    if v < u:
        # Flip so that u/v < 1
        f = True
        u,v = v,u

    # Initialize and check for overflow
    an = v//u
    if an > maxint:
        raise ValueError('Cannot satisfy maxint constraint')

    xn1 = 1;  xn2 = 0
    yn1 = an; yn2 = 1

    v,u = u, v%u

    while u:
        # Compute the next term in the continued fraction expansion.
        v, (an,u) = u, divmod(v,u)

        # Reconstruct the fraction and quit when it is no longer representable.
        xn = an*xn1 + xn2
        if xn > maxint:
            break

        yn = an*yn1 + yn2
        if yn > maxint:
            break

        xn2, xn1, yn2, yn1 = xn1, xn, yn1, yn

    # xn1 and yn1 contain the properly rounded fraction in lowest terms.
    if f:
        return mpq(sign*yn1, xn1)
    else:
        return mpq(sign*xn1, yn1)

