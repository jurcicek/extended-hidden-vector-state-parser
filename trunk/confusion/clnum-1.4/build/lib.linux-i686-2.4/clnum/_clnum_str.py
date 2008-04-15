#-----------------------------------------------------------------------------
# Copyright (c) 2005  Raymond L. Buvel
#
# This file is part of clnum, a Python interface to the Class Library for
# Numbers.  This module provides string manipulation routines which are much
# easier to do in Python than C++.
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
__all__ = ()

#-----------------------------------------------------------------------------
# IMPORTANT NOTE: DO NOT import the clnum module into the global namespace of
# this module.  This module is imported during the initialization of clnum and
# would create a circular import.
#-----------------------------------------------------------------------------
import re

#-----------------------------------------------------------------------------
# Regular expression patterns to match the various types of numbers.

_base_flt = r'[+-]?\d*\.?\d*(?:E[+-]?\d+)?'

# Pattern for degenerate forms that match _base_flt
_degen_lst = [
    r'(^[+-]?\.?E?[+-]?$)',
    r'(^[+-]?\.?E[+-]?\d+$)',
]
mpf_degen_re = re.compile('|'.join(_degen_lst))

integer_re = re.compile(r'^[+-]?\d+$')

mpf_re = re.compile(r'^%s$' % _base_flt)
cmpf_re = re.compile(r'^(%s)(%s)?J$' % (_base_flt, _base_flt))

_base_ra = r'[+-]?\d+/?\d*'

# A trailing slash or divide by zero are not allowed
mpq_degen_re = re.compile(r'.*/0*$')

mpq_re = re.compile(r'^%s$' % _base_ra)
cmpq_re = re.compile(r'^(%s)(%s)?J$' % (_base_ra, _base_ra))

#-----------------------------------------------------------------------------
def _clean_str(s):
    if not isinstance(s, basestring):
        raise ValueError('Input must be a string')

    # The string could be unicode but the C++ routines are expecting a regular
    # string so convert it and remove any leading and trailing white space.
    return str(s).strip().upper()

#-----------------------------------------------------------------------------
def _mpf_clean_str(s):
    s = _clean_str(s)
    if not mpf_re.match(s) or mpf_degen_re.match(s):
        raise ValueError('Invalid floating point format')

    # NOTE: The CLN rejects some forms as valid input so append an
    # acceptable suffix.
    if integer_re.match(s):
        s = s + '.0'
    elif s.endswith('.'):
        s = s + '0'

    return s

#-----------------------------------------------------------------------------
def _mpq_clean_str(s):
    s = _clean_str(s)
    if not mpq_re.match(s) or mpq_degen_re.match(s):
        raise ValueError('Invalid rational format')

    return s

#-----------------------------------------------------------------------------
# NOTE: The CLN library is never allowed to parse a complex input because it
# uses i to designate the imaginary part.  Want to make the interface
# compatible with Python complex conventions.

def _cmpf_clean_str(s):
    s = _clean_str(s)
    m = cmpf_re.match(s)
    msg = 'Invalid complex floating point format'

    if not m:
        # The input could be floating point format in which case the imaginary
        # part is zero.
        try:
            real = _mpf_clean_str(s)
            return real, '0.0'
        except ValueError:
            raise ValueError(msg)

    real, imag = m.groups()

    if mpf_degen_re.match(real):
        raise ValueError(msg)

    if imag:
        if mpf_degen_re.match(imag):
            raise ValueError(msg)
    else:
        # The result is pure imaginary so set the real part to zero.
        imag = real
        real = '0.0'

    # NOTE: The CLN rejects some forms as valid input so append an
    # acceptable suffix.

    if integer_re.match(real):
        real = real + '.0'
    elif real.endswith('.'):
        real = real + '0'

    if integer_re.match(imag):
        imag = imag + '.0'
    elif imag.endswith('.'):
        imag = imag + '0'

    # Pair of strings that convert to floats using CLN syntax.
    return real, imag

#-----------------------------------------------------------------------------
# NOTE: The CLN library is never allowed to parse a complex input because it
# uses i to designate the imaginary part.  Want to make the interface
# compatible with Python complex conventions.

def _cmpq_clean_str(s):
    s = _clean_str(s)
    m = cmpq_re.match(s)
    msg = 'Invalid complex rational format'

    if not m:
        # The input could be rational format in which case the imaginary
        # part is zero.
        try:
            real = _mpq_clean_str(s)
            return real, '0'
        except ValueError:
            raise ValueError(msg)

    real, imag = m.groups()

    if mpq_degen_re.match(real):
        raise ValueError(msg)

    if imag:
        if mpq_degen_re.match(imag):
            raise ValueError(msg)
    else:
        # The result is pure imaginary so set the real part to zero.
        imag = real
        real = '0'

    # Pair of strings that convert to rationals using CLN syntax.
    return real, imag

#-----------------------------------------------------------------------------
def number_str(s, prec=0, prefer_cmpf=False):
    '''Given a string, try to convert it to one of the supported number types.

    The following are applied in order: int, long, mpq, mpf, cmpq, cmpf unless
    prefer_cmpf is True.  Then cmpq and cmpf are swapped.

    Integers (int,long) can have an optional base prefix:
        0x - hex
        0o - octal
        0b - binary

    The floating point forms (mpf,cmpf) accept an optional prec parameter which
    defaults to the current clnum module default.
    '''
    s = _clean_str(s)

    # Save and remove the sign since it interferes with the base recognition.
    sign = 1
    si = s
    if s.startswith('-'):
        sign = -1
        si = s[1:]
    elif s.startswith('+'):
        si = s[1:]

    # Identify the base to use for the conversion.
    bases = {'0X':16, '0O':8, '0B':2}
    prefix = si[:2]
    base = 10
    if prefix in bases:
        si = si[2:]
        base = bases[prefix]

    try:
        return sign*int(si, base)
    except ValueError:
        pass

    try:
        return sign*long(si, base)
    except ValueError:
        pass

    if base != 10:
        raise ValueError('Cannot apply base prefix to non-integers')

    # Import the clnum module here to avoid circular import when clnum is
    # initializing.
    import clnum

    # NOTE: The original string is used from here on because the modified form
    # would cause errors in complex numbers.

    try:
        return clnum.mpq(s)
    except ValueError:
        pass

    try:
        return clnum.mpf(s, prec=prec)
    except ValueError:
        pass

    if prefer_cmpf:
        try:
            return clnum.cmpf(s, prec=prec)
        except ValueError:
            pass

        try:
            return clnum.cmpq(s)
        except ValueError:
            pass

    else:
        try:
            return clnum.cmpq(s)
        except ValueError:
            pass

        try:
            return clnum.cmpf(s, prec=prec)
        except ValueError:
            pass

    raise ValueError('Cannot convert string to a number')

