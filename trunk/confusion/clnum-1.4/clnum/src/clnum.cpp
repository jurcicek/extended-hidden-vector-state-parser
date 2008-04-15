//----------------------------------------------------------------------------
// Copyright (c) 2006  Raymond L. Buvel
// Copyright (c) 2004  Jack W. Crenshaw (see Root Finder section)
//
// This file is part of clnum, a Python interface to the Class Library for
// Numbers.  This module provides the Python type definitions for extended
// precision floating point numbers, rationals, and their complex counterparts.
//
// The clnum module is free software; you can redistribute it and/or modify it
// under the terms of the GNU General Public License as published by the Free
// Software Foundation; either version 2 of the License, or (at your option)
// any later version.
//
// The clnum nodule is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
// or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
// more details.
//
// You should have received a copy of the GNU General Public License along with
// clnum; if not, write to the Free Software Foundation, Inc., 59 Temple Place,
// Suite 330, Boston, MA  02111-1307  USA
//----------------------------------------------------------------------------

// Force Py_ssize_t to be used for s# conversions.
#define PY_SSIZE_T_CLEAN

#include "Python.h"  // Must be first
#include "structmember.h"

#include <cln/cln.h>
#include <string>
#include <sstream>

using namespace cln;

// Make compatible with previous Python versions
#if PY_VERSION_HEX < 0x02050000
typedef int Py_ssize_t;
#define PY_SSIZE_T_MAX INT_MAX
#define PY_SSIZE_T_MIN INT_MIN
#endif

//----------------------------------------------------------------------------
// There is a necessary dependency on the internal representation of a Python
// long integer.  Otherwise, would have to use slow Python API calls to run
// code to break the long apart so it could be converted to a cl_I for further
// processing.  However, the internals are isolated to the following two
// functions which can be updated if the internals change so that the code
// cannot automatically adapt.
#include "longintrepr.h"

static cl_I py_long_to_cl_I(PyLongObject const *v);
static PyObject *py_long_from_cl_I(cl_I const &v);

//----------------------------------------------------------------------------
PyDoc_STRVAR(clnum_doc,
"Class Library for Numbers interface to Python.\n\
\n\
The following types are defined.\n\
    mpf - Extended precicision floating point.\n\
    mpq - Rational numbers.\n\
    cmpf - Complex version of mpf.\n\
    cmpq - Complex version of mpq.\n");

//----------------------------------------------------------------------------
// mpf - Arbitrary precision floating point numbers.  The name choice is to
// make this module so it can be droped into an application that uses gmpy
// without too much modification.

typedef struct {
    PyObject_HEAD
    // Need a pointer here since the Python API doesn't know about C++
    // destructors.  Need to be able to delete the object when the Python
    // object is destroyed or cause memory leaks.
    cl_F *pob_val;
} mpf_object;

#define mpf_check_type(v) (((PyObject*)v)->ob_type == &mpf_type)

//----------------------------------------------------------------------------
// mpq - Arbitrary precision rational numbers.  The name choice is to make this
// module so it can be droped into an application that uses gmpy without too
// much modification.

typedef struct {
    PyObject_HEAD
    // Need a pointer here since the Python API doesn't know about C++
    // destructors.  Need to be able to delete the object when the Python
    // object is destroyed or cause memory leaks.
    cl_RA *pob_val;
} mpq_object;

#define mpq_check_type(v) (((PyObject*)v)->ob_type == &mpq_type)

//----------------------------------------------------------------------------
// cmpf - Arbitrary precision complex floating point numbers.

typedef struct {
    PyObject_HEAD
    // Need a pointer here since the Python API doesn't know about C++
    // destructors.  Need to be able to delete the object when the Python
    // object is destroyed or cause memory leaks.
    cl_N *pob_val;
} cmpf_object;

#define cmpf_check_type(v) (((PyObject*)v)->ob_type == &cmpf_type)

//----------------------------------------------------------------------------
// cmpq - Arbitrary precision complex rational numbers.
//
// Note: This definition may look identical to cmpf.  However, the content of
// the cl_N variable is controlled so that it only holds rational numbers.

typedef struct {
    PyObject_HEAD
    // Need a pointer here since the Python API doesn't know about C++
    // destructors.  Need to be able to delete the object when the Python
    // object is destroyed or cause memory leaks.
    cl_N *pob_val;
} cmpq_object;

#define cmpq_check_type(v) (((PyObject*)v)->ob_type == &cmpq_type)

//----------------------------------------------------------------------------
// Result is true if the object is an exact type.

#define _check_exact(ob) (PyInt_Check(ob) | PyLong_Check(ob) | \
                          mpq_check_type(ob) | cmpq_check_type(ob))

//----------------------------------------------------------------------------
//----------------------------------------------------------------------------
// Current default floating point precision used by the mpf and cmpf types.
// This is mapped to the CLN global default format so that it gets used
// whenever CLN needs to implicitly convert an exact number to floating point.
//
// NOTE: Ideally, the implicit conversion of a Python float to mpf should force
// the cl_F value to contain a cl_DF.  However, that limits the exponent as
// well as the precision.  In addition, mixed arithmetic between cl_LF and
// cl_DF can cause an abort due to overflow.  To avoid this, a minimal cl_LF
// format is used in implicit conversions from Python floats.

#define mpf_prec default_float_format
static float_format_t mpf_prec_for_double;

// Note that the min precision specifies the number of digits where the an mpf
// number uses mpf_prec_for_double.  This choice prevents the CLN library from
// choosing anything but the cl_LF format.

static int const mpf_min_prec = 16;
static int const mpf_str_prec = 16; // Precision for str()

//----------------------------------------------------------------------------
// Many of the print flags are set once so a global variable is used to hold
// them.  Those like the floating point settings are changed before they are
// used.

static cl_print_flags print_flags;

//----------------------------------------------------------------------------
//----------------------------------------------------------------------------

static PyObject *all_pos(PyObject *v);

//----------------------------------------------------------------------------

static int py_float_to_cl_F(PyObject *x, cl_F &y);

static PyObject *anyreal_to_mpf(PyObject *, int);
static PyObject *string_to_mpf(PyObject *, int);

static PyObject *mpf_from_cl_F(cl_F const &v);

static PyObject *mpf_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static void mpf_dealloc(mpf_object *self);

static PyObject *mpf_add(PyObject *v, PyObject *w);
static PyObject *mpf_sub(PyObject *v, PyObject *w);
static PyObject *mpf_mul(PyObject *v, PyObject *w);
static PyObject *mpf_div(PyObject *v, PyObject *w);
static PyObject *mpf_rem(PyObject *v, PyObject *w);
static PyObject *mpf_divmod(PyObject *v, PyObject *w);
static PyObject *mpf_floor_div(PyObject *v, PyObject *w);
static PyObject *mpf_pow(PyObject *px, PyObject *py, PyObject *pz);

static PyObject *mpf_neg(mpf_object *v);
static PyObject *mpf_abs(mpf_object *v);

static int mpf_compare(mpf_object *v, mpf_object *w);
static int mpf_nonzero(mpf_object *v);
static long mpf_hash(mpf_object *v);
static int mpf_coerce(PyObject **pv, PyObject **pw);

static PyObject *mpf_float(mpf_object *v);
static PyObject *mpf_long(mpf_object *v);
static PyObject *mpf_int(mpf_object *v);

static PyObject *mpf_repr(mpf_object *v);
static PyObject *mpf_str(mpf_object *v);

static int mpf_prec_from_cl_F(cl_F const &v);
static float_format_t get_float_format_t(int prec);
static PyObject *mpf_getprec(mpf_object *self, void *closure);
static PyObject *mpf_complex(mpf_object *self);

//----------------------------------------------------------------------------

static PyObject *string_to_mpq(PyObject *v);
static PyObject *anyreal_to_mpq(PyObject *v);

static PyObject *mpq_from_cl_RA(cl_RA const &v);

static PyObject *mpq_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static void mpq_dealloc(mpq_object *self);

static PyObject *mpq_add(PyObject *v, PyObject *w);
static PyObject *mpq_sub(PyObject *v, PyObject *w);
static PyObject *mpq_mul(PyObject *v, PyObject *w);
static PyObject *mpq_div(PyObject *v, PyObject *w);
static PyObject *mpq_rem(PyObject *v, PyObject *w);
static PyObject *mpq_divmod(PyObject *v, PyObject *w);
static PyObject *mpq_floor_div(PyObject *v, PyObject *w);
static PyObject *mpq_pow(PyObject *px, PyObject *py, PyObject *pz);

static PyObject *mpq_neg(mpq_object *v);
static PyObject *mpq_abs(mpq_object *v);

static int mpq_compare(mpq_object *v, mpq_object *w);
static int mpq_nonzero(mpq_object *v);
static long mpq_hash(mpq_object *v);
static int mpq_coerce(PyObject **pv, PyObject **pw);

static PyObject *mpq_float(mpq_object *v);
static PyObject *mpq_long(mpq_object *v);
static PyObject *mpq_int(mpq_object *v);

static PyObject *mpq_repr(mpq_object *v);
static PyObject *mpq_str(mpq_object *v);

static PyObject *mpq_getnumer(mpq_object *self, void *closure);
static PyObject *mpq_getdenom(mpq_object *self, void *closure);
static PyObject *mpq_complex(mpq_object *self);

//----------------------------------------------------------------------------

static int py_complex_to_cl_N(PyObject *x, cl_N &y);

static PyObject *anynum_to_cmpf(PyObject *, int);
static PyObject *string_to_cmpf(PyObject *, int);

static PyObject *cmpf_from_cl_N(cl_N const &v);

static PyObject *cmpf_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static void cmpf_dealloc(cmpf_object *self);

static PyObject *cmpf_add(PyObject *v, PyObject *w);
static PyObject *cmpf_sub(PyObject *v, PyObject *w);
static PyObject *cmpf_mul(PyObject *v, PyObject *w);
static PyObject *cmpf_div(PyObject *v, PyObject *w);
static PyObject *cmpf_pow(PyObject *px, PyObject *py, PyObject *pz);

static PyObject *cmpf_neg(cmpf_object *v);
static PyObject *cmpf_abs(cmpf_object *v);

static PyObject *cmpf_richcompare(PyObject *v, PyObject *w, int op);
static int cmpf_nonzero(cmpf_object *v);
static long cmpf_hash(cmpf_object *v);
static int cmpf_coerce(PyObject **pv, PyObject **pw);

static PyObject *cmpf_repr(cmpf_object *v);
static PyObject *cmpf_str(cmpf_object *v);

static PyObject *cmpf_getprec(cmpf_object *self, void *closure);
static PyObject *cmpf_getreal(cmpf_object *self, void *closure);
static PyObject *cmpf_getimag(cmpf_object *self, void *closure);
static PyObject *cmpf_getphase(cmpf_object *self, void *closure);

static PyObject *cmpf_complex(cmpf_object *self);
static PyObject *cmpf_conjugate(cmpf_object *self);

//----------------------------------------------------------------------------

static int py_complex_to_cl_NQ(PyObject *x, cl_N &y);

static PyObject *anynum_to_cmpq(PyObject *);
static PyObject *string_to_cmpq(PyObject *);

static PyObject *cmpq_from_cl_NQ(cl_N const &v);

static PyObject *cmpq_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static void cmpq_dealloc(cmpq_object *self);

static PyObject *cmpq_add(PyObject *v, PyObject *w);
static PyObject *cmpq_sub(PyObject *v, PyObject *w);
static PyObject *cmpq_mul(PyObject *v, PyObject *w);
static PyObject *cmpq_div(PyObject *v, PyObject *w);
static PyObject *cmpq_pow(PyObject *px, PyObject *py, PyObject *pz);

static PyObject *cmpq_neg(cmpq_object *v);

static PyObject *cmpq_richcompare(PyObject *v, PyObject *w, int op);
static int cmpq_nonzero(cmpq_object *v);
static long cmpq_hash(cmpq_object *v);
static int cmpq_coerce(PyObject **pv, PyObject **pw);

static PyObject *cmpq_repr(cmpq_object *v);
static PyObject *cmpq_str(cmpq_object *v);

static PyObject *cmpq_getreal(cmpq_object *self, void *closure);
static PyObject *cmpq_getimag(cmpq_object *self, void *closure);

static PyObject *cmpq_complex(cmpq_object *self);
static PyObject *cmpq_conjugate(cmpq_object *self);

//----------------------------------------------------------------------------
// Python functions from the _clnum_str module.

static PyObject *_mpf_clean_str;
static PyObject *_mpq_clean_str;
static PyObject *_cmpf_clean_str;
static PyObject *_cmpq_clean_str;

//----------------------------------------------------------------------------
//----------------------------------------------------------------------------
PyDoc_STRVAR(mpf_doc,
"mpf(x) -> extended precision floating point number\n\
mpf(x,prec) -> extended precision floating point number\n\
\n\
Convert a string or number to an extended precision floating point number,\n\
if possible.  The optional prec is the number of decimal digits.");

//----------------------------------------------------------------------------
static PyNumberMethods mpf_as_number = {
    (binaryfunc)mpf_add,    /*nb_add*/
    (binaryfunc)mpf_sub,    /*nb_subtract*/
    (binaryfunc)mpf_mul,    /*nb_multiply*/
    (binaryfunc)mpf_div,    /*nb_divide*/
    (binaryfunc)mpf_rem,    /*nb_remainder*/
    (binaryfunc)mpf_divmod, /*nb_divmod*/
    (ternaryfunc)mpf_pow,   /*nb_power*/
    (unaryfunc)mpf_neg,     /*nb_negative*/
    (unaryfunc)all_pos,     /*nb_positive*/
    (unaryfunc)mpf_abs,     /*nb_absolute*/
    (inquiry)mpf_nonzero,   /*nb_nonzero*/
    0,      /*nb_invert*/
    0,      /*nb_lshift*/
    0,      /*nb_rshift*/
    0,      /*nb_and*/
    0,      /*nb_xor*/
    0,      /*nb_or*/
    (coercion)mpf_coerce,   /*nb_coerce*/
    (unaryfunc)mpf_int,     /*nb_int*/
    (unaryfunc)mpf_long,    /*nb_long*/
    (unaryfunc)mpf_float,   /*nb_float*/
    0,      /* nb_oct */
    0,      /* nb_hex */
    0,      /* nb_inplace_add */
    0,      /* nb_inplace_subtract */
    0,      /* nb_inplace_multiply */
    0,      /* nb_inplace_divide */
    0,      /* nb_inplace_remainder */
    0,      /* nb_inplace_power */
    0,      /* nb_inplace_lshift */
    0,      /* nb_inplace_rshift */
    0,      /* nb_inplace_and */
    0,      /* nb_inplace_xor */
    0,      /* nb_inplace_or */
    mpf_floor_div, /* nb_floor_divide */
    mpf_div,       /* nb_true_divide */
    0,      /* nb_inplace_floor_divide */
    0,      /* nb_inplace_true_divide */
};

//----------------------------------------------------------------------------
static PyGetSetDef mpf_getseters[] = {
    {"prec", 
     (getter)mpf_getprec, NULL,
     "number of decimal digits",
     NULL},
    {NULL}  /* Sentinel */
};

//----------------------------------------------------------------------------
static PyMethodDef mpf_methods[] = {
    {"__complex__", (PyCFunction)mpf_complex, METH_NOARGS},
    {NULL, NULL}  /* sentinel */
};

//----------------------------------------------------------------------------
static PyTypeObject mpf_type = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,
    "clnum.mpf",
    sizeof(mpf_object),
    0,
    (destructor)mpf_dealloc,      /* tp_dealloc */
    0,                            /* tp_print */
    0,                            /* tp_getattr */
    0,                            /* tp_setattr */
    (cmpfunc)mpf_compare,         /* tp_compare */
    (reprfunc)mpf_repr,           /* tp_repr */
    &mpf_as_number,               /* tp_as_number */
    0,                            /* tp_as_sequence */
    0,                            /* tp_as_mapping */
    (hashfunc)mpf_hash,           /* tp_hash */
    0,                            /* tp_call */
    (reprfunc)mpf_str,            /* tp_str */
    PyObject_GenericGetAttr,      /* tp_getattro */
    0,                            /* tp_setattro */
    0,                            /* tp_as_buffer */
    // For now, do not allow subclassing.
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES,        /* tp_flags */
    mpf_doc,            /* tp_doc */
    0,                  /* tp_traverse */
    0,                  /* tp_clear */
    0,                  /* tp_richcompare */
    0,                  /* tp_weaklistoffset */
    0,                  /* tp_iter */
    0,                  /* tp_iternext */
    mpf_methods,        /* tp_methods */
    0,                  /* tp_members */
    mpf_getseters,      /* tp_getset */
    0,                  /* tp_base */
    0,                  /* tp_dict */
    0,                  /* tp_descr_get */
    0,                  /* tp_descr_set */
    0,                  /* tp_dictoffset */
    0,                  /* tp_init */
    0,                  /* tp_alloc */
    mpf_new,            /* tp_new */
};

//----------------------------------------------------------------------------
//----------------------------------------------------------------------------
PyDoc_STRVAR(mpq_doc,
"mpq(x) -> rational number\n\
mpq(numer,denom) -> rational number\n\
\n\
Convert a string or number to a rational number, if possible.\n\
When the numer,denom form is used, both must be integers.");

//----------------------------------------------------------------------------
static PyNumberMethods mpq_as_number = {
    (binaryfunc)mpq_add,    /*nb_add*/
    (binaryfunc)mpq_sub,    /*nb_subtract*/
    (binaryfunc)mpq_mul,    /*nb_multiply*/
    (binaryfunc)mpq_div,    /*nb_divide*/
    (binaryfunc)mpq_rem,    /*nb_remainder*/
    (binaryfunc)mpq_divmod, /*nb_divmod*/
    (ternaryfunc)mpq_pow,   /*nb_power*/
    (unaryfunc)mpq_neg,     /*nb_negative*/
    (unaryfunc)all_pos,     /*nb_positive*/
    (unaryfunc)mpq_abs,     /*nb_absolute*/
    (inquiry)mpq_nonzero,   /*nb_nonzero*/
    0,      /*nb_invert*/
    0,      /*nb_lshift*/
    0,      /*nb_rshift*/
    0,      /*nb_and*/
    0,      /*nb_xor*/
    0,      /*nb_or*/
    (coercion)mpq_coerce,   /*nb_coerce*/
    (unaryfunc)mpq_int,     /*nb_int*/
    (unaryfunc)mpq_long,    /*nb_long*/
    (unaryfunc)mpq_float,   /*nb_float*/
    0,      /* nb_oct */
    0,      /* nb_hex */
    0,      /* nb_inplace_add */
    0,      /* nb_inplace_subtract */
    0,      /* nb_inplace_multiply */
    0,      /* nb_inplace_divide */
    0,      /* nb_inplace_remainder */
    0,      /* nb_inplace_power */
    0,      /* nb_inplace_lshift */
    0,      /* nb_inplace_rshift */
    0,      /* nb_inplace_and */
    0,      /* nb_inplace_xor */
    0,      /* nb_inplace_or */
    mpq_floor_div, /* nb_floor_divide */
    mpq_div,       /* nb_true_divide */
    0,      /* nb_inplace_floor_divide */
    0,      /* nb_inplace_true_divide */
};

//----------------------------------------------------------------------------
static PyGetSetDef mpq_getseters[] = {
    {"numer", 
     (getter)mpq_getnumer, NULL,
     "numerator",
     NULL},
    {"denom", 
     (getter)mpq_getdenom, NULL,
     "denominator",
     NULL},
    {NULL}  /* Sentinel */
};

//----------------------------------------------------------------------------
static PyMethodDef mpq_methods[] = {
    {"__complex__", (PyCFunction)mpq_complex, METH_NOARGS},
    {NULL, NULL}  /* sentinel */
};

//----------------------------------------------------------------------------
static PyTypeObject mpq_type = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,
    "clnum.mpq",
    sizeof(mpq_object),
    0,
    (destructor)mpq_dealloc,      /* tp_dealloc */
    0,                            /* tp_print */
    0,                            /* tp_getattr */
    0,                            /* tp_setattr */
    (cmpfunc)mpq_compare,         /* tp_compare */
    (reprfunc)mpq_repr,           /* tp_repr */
    &mpq_as_number,               /* tp_as_number */
    0,                            /* tp_as_sequence */
    0,                            /* tp_as_mapping */
    (hashfunc)mpq_hash,           /* tp_hash */
    0,                            /* tp_call */
    (reprfunc)mpq_str,            /* tp_str */
    PyObject_GenericGetAttr,      /* tp_getattro */
    0,                            /* tp_setattro */
    0,                            /* tp_as_buffer */
    // For now, do not allow subclassing.
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES,        /* tp_flags */
    mpq_doc,            /* tp_doc */
    0,                  /* tp_traverse */
    0,                  /* tp_clear */
    0,                  /* tp_richcompare */
    0,                  /* tp_weaklistoffset */
    0,                  /* tp_iter */
    0,                  /* tp_iternext */
    mpq_methods,        /* tp_methods */
    0,                  /* tp_members */
    mpq_getseters,      /* tp_getset */
    0,                  /* tp_base */
    0,                  /* tp_dict */
    0,                  /* tp_descr_get */
    0,                  /* tp_descr_set */
    0,                  /* tp_dictoffset */
    0,                  /* tp_init */
    0,                  /* tp_alloc */
    mpq_new,            /* tp_new */
};

//----------------------------------------------------------------------------
//----------------------------------------------------------------------------
PyDoc_STRVAR(cmpf_doc,
"cmpf(z) -> extended precision complex floating point number\n\
cmpf(real,[imag,prec]) -> extended precision complex floating point number\n\
\n\
Convert a string or number to an extended precision complex floating point\n\
number, if possible.  The optional prec is the number of decimal digits.");

//----------------------------------------------------------------------------
static PyNumberMethods cmpf_as_number = {
    (binaryfunc)cmpf_add,    /*nb_add*/
    (binaryfunc)cmpf_sub,    /*nb_subtract*/
    (binaryfunc)cmpf_mul,    /*nb_multiply*/
    (binaryfunc)cmpf_div,    /*nb_divide*/
    0,                       /*nb_remainder*/
    0,                       /*nb_divmod*/
    (ternaryfunc)cmpf_pow,   /*nb_power*/
    (unaryfunc)cmpf_neg,     /*nb_negative*/
    (unaryfunc)all_pos,      /*nb_positive*/
    (unaryfunc)cmpf_abs,     /*nb_absolute*/
    (inquiry)cmpf_nonzero,   /*nb_nonzero*/
    0,      /*nb_invert*/
    0,      /*nb_lshift*/
    0,      /*nb_rshift*/
    0,      /*nb_and*/
    0,      /*nb_xor*/
    0,      /*nb_or*/
    (coercion)cmpf_coerce,   /*nb_coerce*/
    0,      /*nb_int*/
    0,      /*nb_long*/
    0,      /*nb_float*/
    0,      /* nb_oct */
    0,      /* nb_hex */
    0,      /* nb_inplace_add */
    0,      /* nb_inplace_subtract */
    0,      /* nb_inplace_multiply */
    0,      /* nb_inplace_divide */
    0,      /* nb_inplace_remainder */
    0,      /* nb_inplace_power */
    0,      /* nb_inplace_lshift */
    0,      /* nb_inplace_rshift */
    0,      /* nb_inplace_and */
    0,      /* nb_inplace_xor */
    0,      /* nb_inplace_or */
    0,      /* nb_floor_divide */
    cmpf_div,       /* nb_true_divide */
    0,      /* nb_inplace_floor_divide */
    0,      /* nb_inplace_true_divide */
};

//----------------------------------------------------------------------------
static PyGetSetDef cmpf_getseters[] = {
    {"prec", 
     (getter)cmpf_getprec, NULL,
     "number of decimal digits",
     NULL},
    {"real", 
     (getter)cmpf_getreal, NULL,
     "real part",
     NULL},
    {"imag", 
     (getter)cmpf_getimag, NULL,
     "imaginary part",
     NULL},
    {"phase", 
     (getter)cmpf_getphase, NULL,
     "phase angle",
     NULL},
    {NULL}  /* Sentinel */
};

//----------------------------------------------------------------------------
static PyMethodDef cmpf_methods[] = {
    {"conjugate", (PyCFunction)cmpf_conjugate, METH_NOARGS},
    {"__complex__", (PyCFunction)cmpf_complex, METH_NOARGS},
    {NULL, NULL}  /* sentinel */
};

//----------------------------------------------------------------------------
static PyTypeObject cmpf_type = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,
    "clnum.cmpf",
    sizeof(cmpf_object),
    0,
    (destructor)cmpf_dealloc,    /* tp_dealloc */
    0,                           /* tp_print */
    0,                           /* tp_getattr */
    0,                           /* tp_setattr */
    0,                           /* tp_compare */
    (reprfunc)cmpf_repr,         /* tp_repr */
    &cmpf_as_number,             /* tp_as_number */
    0,                           /* tp_as_sequence */
    0,                           /* tp_as_mapping */
    (hashfunc)cmpf_hash,         /* tp_hash */
    0,                           /* tp_call */
    (reprfunc)cmpf_str,          /* tp_str */
    PyObject_GenericGetAttr,     /* tp_getattro */
    0,                           /* tp_setattro */
    0,                           /* tp_as_buffer */
    // For now, do not allow subclassing.
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES,        /* tp_flags */
    cmpf_doc,           /* tp_doc */
    0,                  /* tp_traverse */
    0,                  /* tp_clear */
    cmpf_richcompare,   /* tp_richcompare */
    0,                  /* tp_weaklistoffset */
    0,                  /* tp_iter */
    0,                  /* tp_iternext */
    cmpf_methods,       /* tp_methods */
    0,                  /* tp_members */
    cmpf_getseters,     /* tp_getset */
    0,                  /* tp_base */
    0,                  /* tp_dict */
    0,                  /* tp_descr_get */
    0,                  /* tp_descr_set */
    0,                  /* tp_dictoffset */
    0,                  /* tp_init */
    0,                  /* tp_alloc */
    cmpf_new,           /* tp_new */
};

//----------------------------------------------------------------------------
//----------------------------------------------------------------------------
PyDoc_STRVAR(cmpq_doc,
"cmpq(z) -> complex rational number\n\
cmpq(real[,imag]) -> complex rational number\n\
\n\
Convert a string or number to a complex rational number, if possible.");

//----------------------------------------------------------------------------
static PyNumberMethods cmpq_as_number = {
    (binaryfunc)cmpq_add,    /*nb_add*/
    (binaryfunc)cmpq_sub,    /*nb_subtract*/
    (binaryfunc)cmpq_mul,    /*nb_multiply*/
    (binaryfunc)cmpq_div,    /*nb_divide*/
    0,                       /*nb_remainder*/
    0,                       /*nb_divmod*/
    (ternaryfunc)cmpq_pow,   /*nb_power*/
    (unaryfunc)cmpq_neg,     /*nb_negative*/
    (unaryfunc)all_pos,      /*nb_positive*/
    0,                       /*nb_absolute*/
    (inquiry)cmpq_nonzero,   /*nb_nonzero*/
    0,      /*nb_invert*/
    0,      /*nb_lshift*/
    0,      /*nb_rshift*/
    0,      /*nb_and*/
    0,      /*nb_xor*/
    0,      /*nb_or*/
    (coercion)cmpq_coerce,   /*nb_coerce*/
    0,      /*nb_int*/
    0,      /*nb_long*/
    0,      /*nb_float*/
    0,      /* nb_oct */
    0,      /* nb_hex */
    0,      /* nb_inplace_add */
    0,      /* nb_inplace_subtract */
    0,      /* nb_inplace_multiply */
    0,      /* nb_inplace_divide */
    0,      /* nb_inplace_remainder */
    0,      /* nb_inplace_power */
    0,      /* nb_inplace_lshift */
    0,      /* nb_inplace_rshift */
    0,      /* nb_inplace_and */
    0,      /* nb_inplace_xor */
    0,      /* nb_inplace_or */
    0,      /* nb_floor_divide */
    cmpq_div,       /* nb_true_divide */
    0,      /* nb_inplace_floor_divide */
    0,      /* nb_inplace_true_divide */
};

//----------------------------------------------------------------------------
static PyGetSetDef cmpq_getseters[] = {
    {"real", 
     (getter)cmpq_getreal, NULL,
     "real part",
     NULL},
    {"imag", 
     (getter)cmpq_getimag, NULL,
     "imaginary part",
     NULL},
    {NULL}  /* Sentinel */
};

//----------------------------------------------------------------------------
static PyMethodDef cmpq_methods[] = {
    {"conjugate", (PyCFunction)cmpq_conjugate, METH_NOARGS},
    {"__complex__", (PyCFunction)cmpq_complex, METH_NOARGS},
    {NULL, NULL}  /* sentinel */
};

//----------------------------------------------------------------------------
static PyTypeObject cmpq_type = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,
    "clnum.cmpq",
    sizeof(cmpq_object),
    0,
    (destructor)cmpq_dealloc,    /* tp_dealloc */
    0,                           /* tp_print */
    0,                           /* tp_getattr */
    0,                           /* tp_setattr */
    0,                           /* tp_compare */
    (reprfunc)cmpq_repr,         /* tp_repr */
    &cmpq_as_number,             /* tp_as_number */
    0,                           /* tp_as_sequence */
    0,                           /* tp_as_mapping */
    (hashfunc)cmpq_hash,         /* tp_hash */
    0,                           /* tp_call */
    (reprfunc)cmpq_str,          /* tp_str */
    PyObject_GenericGetAttr,     /* tp_getattro */
    0,                           /* tp_setattro */
    0,                           /* tp_as_buffer */
    // For now, do not allow subclassing.
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES,        /* tp_flags */
    cmpq_doc,           /* tp_doc */
    0,                  /* tp_traverse */
    0,                  /* tp_clear */
    cmpq_richcompare,   /* tp_richcompare */
    0,                  /* tp_weaklistoffset */
    0,                  /* tp_iter */
    0,                  /* tp_iternext */
    cmpq_methods,       /* tp_methods */
    0,                  /* tp_members */
    cmpq_getseters,     /* tp_getset */
    0,                  /* tp_base */
    0,                  /* tp_dict */
    0,                  /* tp_descr_get */
    0,                  /* tp_descr_set */
    0,                  /* tp_dictoffset */
    0,                  /* tp_init */
    0,                  /* tp_alloc */
    cmpq_new,           /* tp_new */
};


//----------------------------------------------------------------------------
// ***** Generic functions
//----------------------------------------------------------------------------

//----------------------------------------------------------------------------
// All types implement +x the same way so use the same routine.
static PyObject *
all_pos(PyObject *v)
{
    Py_INCREF(v);
    return v;
}

//----------------------------------------------------------------------------
// **** depends on the internals of a long ******
#if SHIFT != 15
#error This routine needs to be fixed
#endif

// This constant should be chosen to be around 1000 since measurements show
// that is where the time per digit is least.  It should also result in an
// integral number of 64-bit words so CLN can opimize the operation.
// 15*1024/64 = 240
static int const LONG_BLK_SIZE = 1024;

static cl_I
py_long_to_cl_I(PyLongObject const *v)
{
    cl_I z = 0;
    Py_ssize_t len = v->ob_size;
    int sign = 1;

    if (len == 0)
    {
        // Handle the special case of a zero value.
        return z;
    }

    if (len < 0)
    {
        len = -len;
        sign = -1;
    }

    // Iterate over the digits from the least significant to the most.
    Py_ssize_t i,j,k,m;
    j = len / LONG_BLK_SIZE; // Number of blocks
    k = len % LONG_BLK_SIZE; // Residual
    i = 0; // Starting index
    uintL z_pos = 0;

    // Process all of the whole blocks.
    while (j--)
    {
        cl_I zz = 0;
        cl_byte bits(SHIFT, 0);
        for (m=0; m<LONG_BLK_SIZE; m++)
        {
            zz = dpb(v->ob_digit[i++], zz, bits);
            bits.position += SHIFT;
        }
        z = dpb(zz, z, cl_byte(LONG_BLK_SIZE*SHIFT,z_pos));
        z_pos += LONG_BLK_SIZE*SHIFT;
    }

    // Process the residual digits.
    cl_I zz = 0;
    cl_byte bits(SHIFT, 0);
    for (m=0; m<k; m++)
    {
        zz = dpb(v->ob_digit[i++], zz, bits);
        bits.position += SHIFT;
    }
    z = dpb(zz, z, cl_byte(k*SHIFT,z_pos));

    if (sign < 0)
        return -z;
    else
        return z;
}

//----------------------------------------------------------------------------
// **** depends on the internals of a long ******

static PyObject *
py_long_from_cl_I(cl_I const &v)
{
    if (v == 0)
    {
        return PyLong_FromLong(0L);
    }

    cl_I z = v;  // Get a copy we can modify
    int sign = 1;

    if (z < 0)
    {
        sign = -1;
        z = -z;
    }

    // Note: this gives the exact length of a normalized Python long.
    Py_ssize_t len = (integer_length(z) + SHIFT - 1)/SHIFT;

    PyLongObject *op = _PyLong_New(len);
    if (!op)
    {
        return NULL;
    }

    cl_byte bits(SHIFT,0);
    for (Py_ssize_t i=0; i<len; i++)
    {
        op->ob_digit[i] = cl_I_to_int(ldb(z, bits));
        bits.position += SHIFT;
    }

    // Store the sign and length
    op->ob_size = len*sign;

    return (PyObject *)op;
}


//----------------------------------------------------------------------------
// ***** Extended precision floating point
//----------------------------------------------------------------------------
// Getter for mpf precision.  Used for the prec attribute of mpf objects.
static PyObject *
mpf_getprec(mpf_object *self, void *closure)
{
    return PyInt_FromLong(mpf_prec_from_cl_F(*self->pob_val));
}

//----------------------------------------------------------------------------
static int
mpf_prec_from_cl_F(cl_F const &v)
{
    // The number of bits is log2 of the maximum representable integer.  To
    // convert to number of decimal digits need to divide by log2(10).  The
    // constant is 1/log2(10).
    //
    // Note: some guard digits are subtracted so the result makes sense as the
    // precision request in creating new objects.
    return (int)(float_digits(v)*0.301029995664) - 2;
}

//----------------------------------------------------------------------------
static PyObject *
get_default_precision(PyObject *self, PyObject *args)
{
    int prec = mpf_prec_from_cl_F(cl_float(1, mpf_prec));

    return PyInt_FromLong(prec);
}

//----------------------------------------------------------------------------
static PyObject *
set_default_precision(PyObject *self, PyObject *args)
{
    int prec;

    if (!PyArg_ParseTuple(args, "i:set_default_precision", &prec))
        return NULL;

    mpf_prec = get_float_format_t(prec);

    Py_INCREF(Py_None);
    return Py_None;
}

//----------------------------------------------------------------------------
static float_format_t
get_float_format_t(int prec)
{

    if (prec <= 0)
    {
        return mpf_prec; // Default to global precision
    }

    if (prec <= mpf_min_prec)
    {
        return mpf_prec_for_double;
    }
    else
    {
        return float_format(prec);
    }
}

//----------------------------------------------------------------------------
// The class library for numbers has its own memory management so we need to
// get a pointer to a CLN object and store it in the Python object.  This
// memory must also be released when the Python object is garbage collected.

static PyObject *
mpf_from_cl_F(cl_F const &v)
{
    mpf_object *newob = 0;

    if(!(newob = PyObject_New(mpf_object, &mpf_type)))
        return NULL;

    if (!(newob->pob_val = new cl_F))
    {
        Py_DECREF(newob);
        return PyErr_NoMemory();
    }

    *newob->pob_val = v;

    return (PyObject *)newob;
}

static void
mpf_dealloc(mpf_object *self)
{
    delete self->pob_val;
    self->ob_type->tp_free((PyObject *)self);
}

//----------------------------------------------------------------------------
static PyObject *
mpf_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyObject *x = Py_False; // Integer zero, borrowed reference
    int prec = 0;           // Use default precision

    static char *kwlist[] = {"x", "prec", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|Oi:mpf", kwlist, &x, &prec))
        return NULL;

    if (PyString_Check(x) || PyUnicode_Check(x))
        return string_to_mpf(x, prec);

    return anyreal_to_mpf(x, prec);
}

//----------------------------------------------------------------------------
// Adapted from the routines in floatobject.c
//
// Note: This macro simply returns the value for mpf objects.  Anything else is
// converted to cl_R using the appropriate data type.  When operating on a
// mixed cl_F and an exact type, the CLN library does the right thing and
// converts the exact number to the type and precision of the float.

#define CONVERT_TO_CL_R(obj, clf) \
    if (mpf_check_type(obj))      \
        clf = *((mpf_object *)obj)->pob_val; \
    else if (mpf_convert_to_cl_R(&(obj), &(clf)) < 0) \
        return obj;

static int
mpf_convert_to_cl_R(PyObject **v, cl_R *clf)
{
    PyObject *obj = *v;

    if (PyInt_Check(obj))
    {
        cl_I z = PyInt_AS_LONG(obj);
        *clf = z;
    }
    else if (PyLong_Check(obj))
    {
        cl_I z = py_long_to_cl_I((PyLongObject *)obj);
        *clf = z;
    }
    else if (PyFloat_Check(obj))
    {
        // This is an implicit conversion so use the double precision format.
        cl_F x;
        if (py_float_to_cl_F(obj, x) < 0)
        {
            Py_INCREF(Py_NotImplemented);
            *v = Py_NotImplemented;
            return -1;
        }
        *clf = x;
    }
    else if (mpq_check_type(obj))
    {
        cl_RA q = *((mpq_object *)obj)->pob_val;
        *clf = q;
    }
    else
    {
        Py_INCREF(Py_NotImplemented);
        *v = Py_NotImplemented;
        return -1;
    }
    return 0;
}

//----------------------------------------------------------------------------
// This routine handles checking for overflow conditions that can cause a CLF
// abort.  Also, applies the appropriate precision.
static int
py_float_to_cl_F(PyObject *x, cl_F &y)
{
    double d = PyFloat_AsDouble(x);

    if (Py_IS_INFINITY(d))
        return -1;

    // TODO - should handle NaNs here but have not done enough research to
    // detect them in a platform independent manner.  Doesn't seem to be
    // anything in Python header files that could help.  As a consequence, if
    // the user generates a NaN in Python, it will cause an abort in CLN.

    y = cl_float(d, mpf_prec_for_double);
    return 0;
}

//----------------------------------------------------------------------------
static PyObject *
anyreal_to_mpf(PyObject *v, int prec)
{
    if (mpf_check_type(v) && prec <= 0)
    {
        // Default precision was specified so don't change anything.
        Py_INCREF(v);
        return v;
    }

    float_format_t fmt = get_float_format_t(prec);

    if (mpf_check_type(v))
    {
        // The user has specified a precision so honor that request.
        return mpf_from_cl_F(cl_float(*((mpf_object *)v)->pob_val, fmt));
    }
    else if (PyInt_Check(v))
    {
        cl_I z = PyInt_AS_LONG(v);
        return mpf_from_cl_F(cl_float(z, fmt));
    }
    else if (PyLong_Check(v))
    {
        cl_I z = py_long_to_cl_I((PyLongObject *)v);
        return mpf_from_cl_F(cl_float(z, fmt));
    }
    else if (PyFloat_Check(v))
    {
        cl_F x;
        if (py_float_to_cl_F(v, x) < 0)
        {
            PyErr_SetString(PyExc_ValueError, "mpf: invalid float");
            return NULL;
        }

        if (prec > 0)
        {
            // The user has specified a precision so honor that request.
            return mpf_from_cl_F(cl_float(x, fmt));
        }
        else
        {
            // Default precision was specified so don't make any assumptions
            // and use the format for double precision.
            return mpf_from_cl_F(x);
        }
    }
    else if (mpq_check_type(v))
    {
        cl_RA q = *((mpq_object *)v)->pob_val;
        return mpf_from_cl_F(cl_float(q, fmt));
    }

    PyErr_SetString(PyExc_TypeError, "mpf: unknown type");
    return NULL;
}

//----------------------------------------------------------------------------
static PyObject *
string_to_mpf(PyObject *v, int prec)
{
    // Call Python function to clean up the input string and handle errors.
    PyObject *result = PyObject_CallFunction(_mpf_clean_str, "O", v);
    if (result == NULL)
        return NULL;

    // Set up the read flags to use the precision established by the user.
    float_format_t fmt = get_float_format_t(prec);
    cl_read_flags crf;

    crf.syntax = syntax_lfloat;
    crf.lsyntax = lsyntax_standard;
    crf.float_flags.default_float_format = fmt;
    crf.float_flags.default_lfloat_format = fmt;
    crf.float_flags.mantissa_dependent_float_format = cl_false;

    char const *s = PyString_AS_STRING(result);
    cl_F x = read_float(crf, s, NULL, NULL);
    Py_DECREF(result);

    return mpf_from_cl_F(x);
}

//----------------------------------------------------------------------------
static PyObject *
mpf_add(PyObject *v, PyObject *w)
{
    cl_R a,b;
    CONVERT_TO_CL_R(v, a);
    CONVERT_TO_CL_R(w, b);
    a = a + b;
    return mpf_from_cl_F(cl_float(a));
}

//----------------------------------------------------------------------------
static PyObject *
mpf_sub(PyObject *v, PyObject *w)
{
    cl_R a,b;
    CONVERT_TO_CL_R(v, a);
    CONVERT_TO_CL_R(w, b);
    a = a - b;
    return mpf_from_cl_F(cl_float(a));
}

//----------------------------------------------------------------------------
static PyObject *
mpf_mul(PyObject *v, PyObject *w)
{
    cl_R a,b;
    CONVERT_TO_CL_R(v, a);
    CONVERT_TO_CL_R(w, b);
    a = a * b;

    // Note: the CLN library returns an exact type if an exact zero is used in
    // the calculation.  Need to make sure the conversion to float preserves
    // the precision of the floating point input.
    if ((a == 0) && (_check_exact(v) || _check_exact(w)))
    {
        // The result is zero and one of the operands is exact.
        if (mpf_check_type(v))
        {
            return mpf_from_cl_F(cl_float(0, *((mpf_object *)v)->pob_val));
        }
        if (mpf_check_type(w))
        {
            return mpf_from_cl_F(cl_float(0, *((mpf_object *)w)->pob_val));
        }
    }
    return mpf_from_cl_F(cl_float(a));
}

//----------------------------------------------------------------------------
static PyObject *
mpf_div(PyObject *v, PyObject *w)
{
    cl_R a,b;
    CONVERT_TO_CL_R(v, a);
    CONVERT_TO_CL_R(w, b);
    if (b == 0.0) {
        PyErr_SetString(PyExc_ZeroDivisionError, "mpf division");
        return NULL;
    }

    a = a / b;

    // Note: the CLN library returns an exact type if an exact zero is used in
    // the calculation.  Need to make sure the conversion to float preserves
    // the precision of the floating point input.
    if ((a == 0) && _check_exact(v))
    {
        // The result is zero and the first operand is exact.
        return mpf_from_cl_F(cl_float(0, *((mpf_object *)w)->pob_val));
    }
    return mpf_from_cl_F(cl_float(a));
}

//----------------------------------------------------------------------------
static PyObject *
mpf_rem(PyObject *v, PyObject *w)
{
    cl_R a,b;
    CONVERT_TO_CL_R(v, a);
    CONVERT_TO_CL_R(w, b);
    if (b == 0.0) {
        PyErr_SetString(PyExc_ZeroDivisionError, "mpf remainder");
        return NULL;
    }

    cl_F q = ffloor(a, b);

    // Note: the CLN library returns an exact type if an exact zero is used in
    // the calculation.  Need to make sure the conversion to float preserves
    // the precision of the floating point input.
    if ((q == 0.0) && _check_exact(v))
    {
        // The result is zero and the first operand is exact.
        q = cl_float(0, *((mpf_object *)w)->pob_val);
    }

    cl_F r = cl_float(a - q*b);

    return mpf_from_cl_F(r);
}

//----------------------------------------------------------------------------
static PyObject *
mpf_divmod(PyObject *v, PyObject *w)
{
    cl_R a,b;
    CONVERT_TO_CL_R(v, a);
    CONVERT_TO_CL_R(w, b);
    if (b == 0.0) {
        PyErr_SetString(PyExc_ZeroDivisionError, "mpf divmod");
        return NULL;
    }

    cl_F q = ffloor(a, b);

    // Note: the CLN library returns an exact type if an exact zero is used in
    // the calculation.  Need to make sure the conversion to float preserves
    // the precision of the floating point input.
    if ((q == 0.0) && _check_exact(v))
    {
        // The result is zero and the first operand is exact.
        q = cl_float(0, *((mpf_object *)w)->pob_val);
    }

    cl_F r = cl_float(a - q*b);

    PyObject *result = PyTuple_New(2);
    PyTuple_SET_ITEM(result, 0, mpf_from_cl_F(q));
    PyTuple_SET_ITEM(result, 1, mpf_from_cl_F(r));
    return result;
}

//----------------------------------------------------------------------------
static PyObject *
mpf_floor_div(PyObject *v, PyObject *w)
{
    cl_R a,b;
    CONVERT_TO_CL_R(v, a);
    CONVERT_TO_CL_R(w, b);
    if (b == 0.0) {
        PyErr_SetString(PyExc_ZeroDivisionError, "mpf floor division");
        return NULL;
    }

    cl_F q = ffloor(a, b);

    // Note: the CLN library returns an exact type if an exact zero is used in
    // the calculation.  Need to make sure the conversion to float preserves
    // the precision of the floating point input.
    if ((q == 0.0) && _check_exact(v))
    {
        // The result is zero and the first operand is exact.
        q = cl_float(0, *((mpf_object *)w)->pob_val);
    }

    return mpf_from_cl_F(q);
}

//----------------------------------------------------------------------------
static PyObject *
mpf_pow(PyObject *px, PyObject *py, PyObject *pz)
{
    if (pz != Py_None)
    {
        PyErr_SetString(PyExc_TypeError, "pow() 3rd argument not "
            "allowed unless all arguments are integers");
        return NULL;
    }

    cl_R x, y;
    CONVERT_TO_CL_R(px, x);
    CONVERT_TO_CL_R(py, y);

    // There is a bug in CLN that is triggered when the first argument is an
    // exact number.  Explicitly transform to float in this case.  Note this
    // can only happen when the second argument is mpf.
    if (PyInt_Check(px) | PyLong_Check(px) | mpq_check_type(px))
    {
        x = cl_float(x, cl_float(y));
    }

    // Sort out special cases here instead of relying on library.
    // This makes sure they are defined the way Python defines them.
    //
    // Note: don't degrade the precision if one of the special cases.
    if (y == 0.0)
    {
        cl_F fx = cl_float(x);
        cl_F fy = cl_float(y);
        // x**0 is 1, even 0**0
        if (float_digits(fx) < float_digits(fy))
        {
            return mpf_from_cl_F(cl_float(1, fy));
        }
        else
        {
            return mpf_from_cl_F(cl_float(1, fx));
        }
    }
    if (x == 0.0)
    {
        // 0**y is error if y<0, else 0
        if (y < 0.0) {
            PyErr_SetString(PyExc_ZeroDivisionError,
                    "0.0 cannot be raised to a negative power");
            return NULL;
        }
        cl_F fx = cl_float(x);
        cl_F fy = cl_float(y);
        if (float_digits(fx) < float_digits(fy))
        {
            return mpf_from_cl_F(cl_float(0, fy));
        }
        else
        {
            return mpf_from_cl_F(cl_float(0, fx));
        }
    }

    // Now we rely on CLN to get the math correct.
    //
    // Apply the complex version of this operation and return the result if
    // real.  Otherwise, it is an error.
    cl_N z = expt((cl_N)x, (cl_N)y);

    if (imagpart(z) != 0.0)
    {
        PyErr_SetString(PyExc_ValueError, "pow() result is complex");
        return NULL;
    }

    return mpf_from_cl_F(cl_float(realpart(z)));
}

//----------------------------------------------------------------------------
static PyObject *
mpf_neg(mpf_object *v)
{
    return mpf_from_cl_F( -(*v->pob_val));
}

//----------------------------------------------------------------------------
static PyObject *
mpf_abs(mpf_object *v)
{
    cl_F a = *v->pob_val;
    if (a < 0.0)
    {
        return mpf_from_cl_F(-a);
    }
    Py_INCREF(v);
    return (PyObject *)v;
}

//----------------------------------------------------------------------------
static PyObject *
mpf_float(mpf_object *v)
{
    return PyFloat_FromDouble(double_approx(*v->pob_val));
}

//----------------------------------------------------------------------------
static PyObject *
mpf_long(mpf_object *v)
{
    return py_long_from_cl_I(truncate1(*v->pob_val));
}

//----------------------------------------------------------------------------
static PyObject *
mpf_int(mpf_object *v)
{
    cl_I z = truncate1(*v->pob_val);

    if (LONG_MIN <= z && z <= LONG_MAX)
    {
        return PyInt_FromLong(cl_I_to_long(z));
    }
    return py_long_from_cl_I(z);
}

//----------------------------------------------------------------------------
static int
mpf_compare(mpf_object *v, mpf_object *w)
{
    cl_F a = *v->pob_val;
    cl_F b = *w->pob_val;

    return compare(a, b);
}

//----------------------------------------------------------------------------
static int
mpf_nonzero(mpf_object *v)
{
    return !zerop(*v->pob_val);
}

//----------------------------------------------------------------------------
static int
mpf_coerce(PyObject **pv, PyObject **pw)
{
    // This is the easy case, if the other type is also an mpf the two types
    // are considered the same even if they have different precisions.  The
    // operations performed on these values will operate correctly because the
    // CLN library will handle them.
    if (mpf_check_type(*pw))
    {
        Py_INCREF(*pv);
        Py_INCREF(*pw);
        return 0;
    }

    // Get the value of self so the format of the new object is the same.
    cl_F a = *((mpf_object *)(*pv))->pob_val;

    if (PyInt_Check(*pw))
    {
        cl_I z = PyInt_AS_LONG(*pw);
        *pw = mpf_from_cl_F(cl_float(z, a));
        Py_INCREF(*pv);
        return 0;
    }
    else if (PyLong_Check(*pw))
    {
        cl_I z = py_long_to_cl_I((PyLongObject *)(*pw));
        *pw = mpf_from_cl_F(cl_float(z, a));
        Py_INCREF(*pv);
        return 0;
    }
    else if (PyFloat_Check(*pw))
    {
        // This is an implicit conversion so use the double precision format.
        cl_F x;
        if (py_float_to_cl_F(*pw, x) < 0)
            return 1;

        *pw = mpf_from_cl_F(x);
        Py_INCREF(*pv);
        return 0;
    }
    else if (mpq_check_type(*pw))
    {
        cl_RA q = *((mpq_object *)(*pw))->pob_val;
        *pw = mpf_from_cl_F(cl_float(q, a));
        Py_INCREF(*pv);
        return 0;
    }

    // Don't recognize the other type
    return 1;
}

//----------------------------------------------------------------------------
// Since we want mpf numbers to be interoperable with Python numbers, should
// use the same hash algorithm as Python floats on a double approximation of
// the mpf.

static long
mpf_hash(mpf_object *v)
{
    return _Py_HashDouble(double_approx(*v->pob_val));
}

//----------------------------------------------------------------------------
static PyObject *
mpf_repr(mpf_object *v)
{
    cl_F x = *v->pob_val;

    // Force the use of the E notation so that the strings are compatible with
    // a Python float.
    print_flags.default_float_format = float_format(x);

    std::ostringstream out_stream;
    out_stream << "mpf('";
    print_float(out_stream, print_flags, x);
    out_stream << "',";
    out_stream << mpf_prec_from_cl_F(x);
    out_stream << ")";

    std::string s = out_stream.str();
    std::size_t i = s.find('E');
    if (i != std::string::npos)
        s[i] = 'e';

    return PyString_FromString(s.c_str());
}

//----------------------------------------------------------------------------
static PyObject *
mpf_str(mpf_object *v)
{
    // Convert the value to a format that doesn't display all digits that are
    // possible.  This should make the results a bit more readable.  The user
    // can get full precision by using repr() instead of str().
    float_format_t fmt = float_format(mpf_str_prec);
    cl_F x = cl_float(*v->pob_val, fmt);

    // Force the use of the E notation so that the strings are compatible with
    // a Python float.
    print_flags.default_float_format = fmt;

    std::ostringstream out_stream;
    print_float(out_stream, print_flags, x);

    std::string s = out_stream.str();
    std::size_t i = s.find('E');
    if (i != std::string::npos)
        s[i] = 'e';

    return PyString_FromString(s.c_str());
}

//----------------------------------------------------------------------------
static PyObject *
mpf_complex(mpf_object *self)
{
    return PyComplex_FromDoubles(double_approx(*self->pob_val), 0.0);
}

//----------------------------------------------------------------------------
// ***** Rational Numbers
//----------------------------------------------------------------------------
// The class library for numbers has its own memory management so we need to
// get a pointer to a CLN object and store it in the Python object.  This
// memory must also be released when the Python object is garbage collected.

static PyObject *
mpq_from_cl_RA(cl_RA const &v)
{
    mpq_object *newob = 0;

    if(!(newob = PyObject_New(mpq_object, &mpq_type)))
        return NULL;

    if (!(newob->pob_val = new cl_RA))
    {
        Py_DECREF(newob);
        return PyErr_NoMemory();
    }

    *newob->pob_val = v;

    return (PyObject *)newob;
}

static void
mpq_dealloc(mpq_object *self)
{
    delete self->pob_val;
    self->ob_type->tp_free((PyObject *)self);
}

//----------------------------------------------------------------------------
static PyObject *
mpq_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyObject *numer = Py_False; // Integer zero, borrowed reference
    PyObject *denom = Py_None;  // Borrowed reference

    static char *kwlist[] = {"numer", "denom", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OO:mpq", kwlist,
                &numer, &denom))
        return NULL;

    if (denom == Py_None)
    {
        if (PyString_Check(numer) || PyUnicode_Check(numer))
            return string_to_mpq(numer);

        return anyreal_to_mpq(numer);
    }

    // Now both the numerator and denominator MUST be integers.
    cl_RA N, D;

    if (PyInt_Check(numer))
    {
        N = PyInt_AS_LONG(numer);
    }
    else if (PyLong_Check(numer))
    {
        N = py_long_to_cl_I((PyLongObject *)numer);
    }
    else
    {
        PyErr_SetString(PyExc_TypeError, "numerator must be an integer");
        return NULL;
    }

    if (PyInt_Check(denom))
    {
        D = PyInt_AS_LONG(denom);
    }
    else if (PyLong_Check(denom))
    {
        D = py_long_to_cl_I((PyLongObject *)denom);
    }
    else
    {
        PyErr_SetString(PyExc_TypeError, "denominator must be an integer");
        return NULL;
    }

    if (D == 0)
    {
        PyErr_SetString(PyExc_ZeroDivisionError, "zero denominator");
        return NULL;
    }

    return mpq_from_cl_RA(N/D);
}

//----------------------------------------------------------------------------
// Adapted from the routines in floatobject.c
//
// Note: This macro simply returns the value for mpq objects.  Anything else
// must be an integer which gets converted to cl_RA.  Numbers that are not
// integers or rationals are either complex or considered non-exact.

#define CONVERT_TO_CL_RA(obj, clq) \
    if (mpq_check_type(obj))       \
        clq = *((mpq_object *)obj)->pob_val; \
    else if (mpq_convert_to_cl_RA(&(obj), &(clq)) < 0) \
        return obj;

static int
mpq_convert_to_cl_RA(PyObject **v, cl_RA *clq)
{
    PyObject *obj = *v;

    if (PyInt_Check(obj))
    {
        *clq = PyInt_AS_LONG(obj);
    }
    else if (PyLong_Check(obj))
    {
        *clq = py_long_to_cl_I((PyLongObject *)obj);
    }
    else
    {
        Py_INCREF(Py_NotImplemented);
        *v = Py_NotImplemented;
        return -1;
    }
    return 0;
}

//----------------------------------------------------------------------------
// This function is called only when the user has called for an explicit
// conversion to rational.  Consequently, any real value can be converted.
static PyObject *
anyreal_to_mpq(PyObject *v)
{
    if (mpq_check_type(v))
    {
        Py_INCREF(v);
        return v;
    }
    else if (mpf_check_type(v))
    {
        return mpq_from_cl_RA(rationalize(*((mpf_object *)v)->pob_val));
    }
    else if (PyInt_Check(v))
    {
        cl_I z = PyInt_AS_LONG(v);
        return mpq_from_cl_RA(z);
    }
    else if (PyLong_Check(v))
    {
        cl_I z = py_long_to_cl_I((PyLongObject *)v);
        return mpq_from_cl_RA(z);
    }
    else if (PyFloat_Check(v))
    {
        cl_F x;
        if (py_float_to_cl_F(v, x) < 0)
        {
            PyErr_SetString(PyExc_ValueError, "mpq: invalid float");
            return NULL;
        }
        return mpq_from_cl_RA(rationalize(x));
    }

    PyErr_SetString(PyExc_TypeError, "mpq: unknown type");
    return NULL;
}

//----------------------------------------------------------------------------
static PyObject *
string_to_mpq(PyObject *v)
{
    // Call Python function to clean up the input string and handle errors.
    PyObject *result = PyObject_CallFunction(_mpq_clean_str, "O", v);
    if (result == NULL)
        return NULL;

    cl_read_flags crf;
    crf.syntax = syntax_rational;
    crf.lsyntax = lsyntax_standard;
    crf.rational_base = 10;

    char const *s = PyString_AS_STRING(result);
    cl_RA x = read_rational(crf, s, NULL, NULL);
    Py_DECREF(result);

    return mpq_from_cl_RA(x);
}

//----------------------------------------------------------------------------
static PyObject *
mpq_add(PyObject *v, PyObject *w)
{
    cl_RA a,b;
    CONVERT_TO_CL_RA(v, a);
    CONVERT_TO_CL_RA(w, b);
    a = a + b;
    return mpq_from_cl_RA(a);
}

//----------------------------------------------------------------------------
static PyObject *
mpq_sub(PyObject *v, PyObject *w)
{
    cl_RA a,b;
    CONVERT_TO_CL_RA(v, a);
    CONVERT_TO_CL_RA(w, b);
    a = a - b;
    return mpq_from_cl_RA(a);
}

//----------------------------------------------------------------------------
static PyObject *
mpq_mul(PyObject *v, PyObject *w)
{
    cl_RA a,b;
    CONVERT_TO_CL_RA(v, a);
    CONVERT_TO_CL_RA(w, b);
    a = a * b;
    return mpq_from_cl_RA(a);
}

//----------------------------------------------------------------------------
static PyObject *
mpq_div(PyObject *v, PyObject *w)
{
    cl_RA a,b;
    CONVERT_TO_CL_RA(v, a);
    CONVERT_TO_CL_RA(w, b);
    if (b == 0) {
        PyErr_SetString(PyExc_ZeroDivisionError, "mpq division");
        return NULL;
    }

    a = a / b;
    return mpq_from_cl_RA(a);
}

//----------------------------------------------------------------------------
static PyObject *
mpq_rem(PyObject *v, PyObject *w)
{
    cl_RA a,b;
    CONVERT_TO_CL_RA(v, a);
    CONVERT_TO_CL_RA(w, b);
    if (b == 0) {
        PyErr_SetString(PyExc_ZeroDivisionError, "mpq remainder");
        return NULL;
    }

    cl_RA r = a - floor1(a, b)*b;

    return mpq_from_cl_RA(r);
}

//----------------------------------------------------------------------------
static PyObject *
mpq_divmod(PyObject *v, PyObject *w)
{
    cl_RA a,b;
    CONVERT_TO_CL_RA(v, a);
    CONVERT_TO_CL_RA(w, b);
    if (b == 0) {
        PyErr_SetString(PyExc_ZeroDivisionError, "mpq divmod");
        return NULL;
    }

    cl_I q = floor1(a, b);
    cl_RA r = a - q*b;

    PyObject *result = PyTuple_New(2);
    PyTuple_SET_ITEM(result, 0, mpq_from_cl_RA(q));
    PyTuple_SET_ITEM(result, 1, mpq_from_cl_RA(r));
    return result;
}

//----------------------------------------------------------------------------
static PyObject *
mpq_floor_div(PyObject *v, PyObject *w)
{
    cl_RA a,b;
    CONVERT_TO_CL_RA(v, a);
    CONVERT_TO_CL_RA(w, b);
    if (b == 0) {
        PyErr_SetString(PyExc_ZeroDivisionError, "mpq remainder");
        return NULL;
    }

    cl_I q = floor1(a, b);

    return mpq_from_cl_RA(q);
}

//----------------------------------------------------------------------------
static PyObject *
mpq_pow(PyObject *px, PyObject *py, PyObject *pz)
{
    if (pz != Py_None)
    {
        PyErr_SetString(PyExc_TypeError, "pow() 3rd argument not "
            "allowed unless all arguments are integers");
        return NULL;
    }

    cl_RA x, y;
    CONVERT_TO_CL_RA(px, x);
    CONVERT_TO_CL_RA(py, y);

    // Sort out special cases here instead of relying on library.
    // This makes sure they are defined the way Python defines them.
    if (y == 0)
    {
        // x**0 is 1, even 0**0
        return mpq_from_cl_RA(1);
    }

    if (x == 0)
    {
        // 0**y is error if y<0, else 0
        if (y < 0) {
            PyErr_SetString(PyExc_ZeroDivisionError,
                    "0 cannot be raised to a negative power");
            return NULL;
        }
        return mpq_from_cl_RA(0);
    }

    if (denominator(y) != 1)
    {
        PyErr_SetString(PyExc_ValueError, "pow(x,y) y must be an integer");
        return NULL;
    }

    // Now we rely on CLN to get the math correct.
    cl_RA q = expt(x, numerator(y));

    return mpq_from_cl_RA(q);
}

//----------------------------------------------------------------------------
static PyObject *
mpq_neg(mpq_object *v)
{
    return mpq_from_cl_RA( -(*v->pob_val));
}

//----------------------------------------------------------------------------
static PyObject *
mpq_abs(mpq_object *v)
{
    cl_RA a = *v->pob_val;
    if (a < 0)
    {
        return mpq_from_cl_RA(-a);
    }
    Py_INCREF(v);
    return (PyObject *)v;
}

//----------------------------------------------------------------------------
static PyObject *
mpq_float(mpq_object *v)
{
    return PyFloat_FromDouble(double_approx(*v->pob_val));
}

//----------------------------------------------------------------------------
static PyObject *
mpq_long(mpq_object *v)
{
    return py_long_from_cl_I(truncate1(*v->pob_val));
}

//----------------------------------------------------------------------------
static PyObject *
mpq_int(mpq_object *v)
{
    cl_I z = truncate1(*v->pob_val);

    if (LONG_MIN <= z && z <= LONG_MAX)
    {
        return PyInt_FromLong(cl_I_to_long(z));
    }
    return py_long_from_cl_I(z);
}

//----------------------------------------------------------------------------
static int
mpq_compare(mpq_object *v, mpq_object *w)
{
    cl_RA a = *v->pob_val;
    cl_RA b = *w->pob_val;

    return compare(a, b);
}

//----------------------------------------------------------------------------
static int
mpq_nonzero(mpq_object *v)
{
    return !zerop(*v->pob_val);
}

//----------------------------------------------------------------------------
static int
mpq_coerce(PyObject **pv, PyObject **pw)
{
    if (mpq_check_type(*pw))
    {
        Py_INCREF(*pv);
        Py_INCREF(*pw);
        return 0;
    }

    if (PyInt_Check(*pw))
    {
        cl_I z = PyInt_AS_LONG(*pw);
        *pw = mpq_from_cl_RA(z);
        Py_INCREF(*pv);
        return 0;
    }
    else if (PyLong_Check(*pw))
    {
        cl_I z = py_long_to_cl_I((PyLongObject *)(*pw));
        *pw = mpq_from_cl_RA(z);
        Py_INCREF(*pv);
        return 0;
    }

    // Only exact numbers can be converted.
    return 1;
}

//----------------------------------------------------------------------------
// Since we want mpq numbers to be interoperable with Python numbers, should
// use the same hash algorithm as Python floats on a double approximation of
// the mpq.

static long
mpq_hash(mpq_object *v)
{
    return _Py_HashDouble(double_approx(*v->pob_val));
}

//----------------------------------------------------------------------------
static PyObject *
mpq_repr(mpq_object *v)
{
    std::ostringstream out_stream;

    out_stream << "mpq(";
    print_rational(out_stream, print_flags, numerator(*v->pob_val));
    out_stream << ",";
    print_rational(out_stream, print_flags, denominator(*v->pob_val));
    out_stream << ")";

    return PyString_FromString(out_stream.str().c_str());
}

//----------------------------------------------------------------------------
static PyObject *
mpq_str(mpq_object *v)
{
    std::ostringstream out_stream;

    print_rational(out_stream, print_flags, *v->pob_val);

    return PyString_FromString(out_stream.str().c_str());
}

//----------------------------------------------------------------------------
static PyObject *
mpq_getnumer(mpq_object *self, void *closure)
{
    cl_I z = numerator(*self->pob_val);

    if (LONG_MIN <= z && z <= LONG_MAX)
    {
        return PyInt_FromLong(cl_I_to_long(z));
    }
    return py_long_from_cl_I(z);
}

//----------------------------------------------------------------------------
static PyObject *
mpq_getdenom(mpq_object *self, void *closure)
{
    cl_I z = denominator(*self->pob_val);

    if (LONG_MIN <= z && z <= LONG_MAX)
    {
        return PyInt_FromLong(cl_I_to_long(z));
    }
    return py_long_from_cl_I(z);
}

//----------------------------------------------------------------------------
static PyObject *
mpq_complex(mpq_object *self)
{
    return PyComplex_FromDoubles(double_approx(*self->pob_val), 0.0);
}

//----------------------------------------------------------------------------
//*************** Complex floats
//----------------------------------------------------------------------------

//----------------------------------------------------------------------------
// This routine handles checking for overflow conditions that can cause a CLF
// abort.  Also, applies the appropriate precision.
static int
py_complex_to_cl_N(PyObject *x, cl_N &y)
{
    double dr = PyComplex_RealAsDouble(x);
    double di = PyComplex_ImagAsDouble(x);

    if (Py_IS_INFINITY(dr) || Py_IS_INFINITY(di))
        return -1;

    // TODO - should handle NaNs here but have not done enough research to
    // detect them in a platform independent manner.  Doesn't seem to be
    // anything in Python header files that could help.  As a consequence, if
    // the user generates a NaN in Python, it will cause an abort in CLN.

    cl_F real = cl_float(dr, mpf_prec_for_double);
    cl_F imag = cl_float(di, mpf_prec_for_double);
    y = complex(real, imag);
    return 0;
}


//----------------------------------------------------------------------------
// The class library for numbers has its own memory management so we need to
// get a pointer to a CLN object and store it in the Python object.  This
// memory must also be released when the Python object is garbage collected.

static PyObject *
cmpf_from_cl_N(cl_N const &v)
{
    cmpf_object *newob = 0;

    if(!(newob = PyObject_New(cmpf_object, &cmpf_type)))
        return NULL;

    if (!(newob->pob_val = new cl_N))
    {
        Py_DECREF(newob);
        return PyErr_NoMemory();
    }

    *newob->pob_val = v;

    return (PyObject *)newob;
}

static void
cmpf_dealloc(cmpf_object *self)
{
    delete self->pob_val;
    self->ob_type->tp_free((PyObject *)self);
}

//----------------------------------------------------------------------------
static PyObject *
cmpf_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyObject *real = Py_False; // Integer zero, borrowed reference
    PyObject *imag = Py_None;  // Borrowed reference
    int prec = 0;              // Use default precision

    static char *kwlist[] = {"real", "imag", "prec", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOi:cmpf", kwlist,
                &real, &imag, &prec))
        return NULL;

    if (imag == Py_None)
    {
        if (PyString_Check(real) || PyUnicode_Check(real))
            return string_to_cmpf(real, prec);

        return anynum_to_cmpf(real, prec);
    }

    // At this point, both the real and imaginary parts must be some kind of
    // real values.  Coerce them to mpf type with the specified precision.

    mpf_object *ob = (mpf_object *)anyreal_to_mpf(real, prec);
    if (ob == NULL)
        return NULL;

    cl_F x = *ob->pob_val;
    Py_DECREF(ob);

    ob = (mpf_object *)anyreal_to_mpf(imag, prec);
    if (ob == NULL)
        return NULL;

    cl_F y = *ob->pob_val;
    Py_DECREF(ob);

    // Normalize the precision to the lowest value.  Note that this only
    // happens when the default precision is specified.

    uintL ix = float_digits(x);
    uintL iy = float_digits(y);

    if (ix < iy)
    {
        y = cl_float(y, x);
    }
    else if (ix > iy)
    {
        x = cl_float(x, y);
    }

    return cmpf_from_cl_N(complex(x,y));
}

//----------------------------------------------------------------------------
// Adapted from the routines in floatobject.c
//
// Note: This macro simply returns the value for cmpf objects.  Anything else
// is converted to cl_N using the appropriate data type.  When operating on a
// mixed cl_F and an exact type, the CLN library does the right thing and
// converts the exact number to the type and precision of the float.
//
// Exact numbers are converted using the simplest form accepted by the CLN
// library.

#define CONVERT_TO_CL_N(obj, cln) \
    if (cmpf_check_type(obj))     \
        cln = *((cmpf_object *)obj)->pob_val; \
    else if (cmpf_convert_to_cl_N(&(obj), &(cln)) < 0) \
        return obj;

static int
cmpf_convert_to_cl_N(PyObject **v, cl_N *cln)
{
    PyObject *obj = *v;

    if (PyInt_Check(obj))
    {
        cl_I z = PyInt_AS_LONG(obj);
        *cln = z;
    }
    else if (PyLong_Check(obj))
    {
        cl_I z = py_long_to_cl_I((PyLongObject *)obj);
        *cln = z;
    }
    else if (PyFloat_Check(obj))
    {
        // This is an implicit conversion so use the double precision format.
        cl_F x;
        if (py_float_to_cl_F(obj, x) < 0)
        {
            Py_INCREF(Py_NotImplemented);
            *v = Py_NotImplemented;
            return -1;
        }
        *cln = complex(x, cl_float(0.0,x));
    }
    else if (PyComplex_Check(obj))
    {
        // This is an implicit conversion so use the double precision format.
        cl_N z;
        if (py_complex_to_cl_N(obj, z) < 0)
        {
            Py_INCREF(Py_NotImplemented);
            *v = Py_NotImplemented;
            return -1;
        }
        *cln = z;
    }
    else if (mpf_check_type(obj))
    {
        cl_F x = *((mpf_object *)obj)->pob_val;
        *cln = complex(x, cl_float(0.0,x));
    }
    else if (mpq_check_type(obj))
    {
        cl_RA q = *((mpq_object *)obj)->pob_val;
        *cln = q;
    }
    else if (cmpq_check_type(obj))
    {
        cl_N z = *((cmpq_object *)obj)->pob_val;
        *cln = z;
    }
    else
    {
        Py_INCREF(Py_NotImplemented);
        *v = Py_NotImplemented;
        return -1;
    }
    return 0;
}

//----------------------------------------------------------------------------
static PyObject *
anynum_to_cmpf(PyObject *v, int prec)
{
    if (cmpf_check_type(v) && prec <= 0)
    {
        // Default precision was specified so don't change anything.
        Py_INCREF(v);
        return v;
    }

    float_format_t fmt = get_float_format_t(prec);

    if (cmpf_check_type(v))
    {
        // The user has specified a precision so honor that request.
        cl_N z = *((cmpf_object *)v)->pob_val;
        cl_F x = cl_float(realpart(z), fmt);
        cl_F y = cl_float(imagpart(z), fmt);
        return cmpf_from_cl_N(complex(x,y));
    }
    else if (PyInt_Check(v))
    {
        cl_I z = PyInt_AS_LONG(v);
        return cmpf_from_cl_N(complex(cl_float(z,fmt),cl_float(0.0,fmt)));
    }
    else if (PyLong_Check(v))
    {
        cl_I z = py_long_to_cl_I((PyLongObject *)v);
        return cmpf_from_cl_N(complex(cl_float(z,fmt),cl_float(0.0,fmt)));
    }
    else if (PyFloat_Check(v))
    {
        cl_F x;
        if (py_float_to_cl_F(v, x) < 0)
        {
            PyErr_SetString(PyExc_ValueError, "cmpf: invalid float");
            return NULL;
        }

        if (prec > 0)
        {
            // The user has specified a precision so honor that request.
            return cmpf_from_cl_N(complex(cl_float(x,fmt),cl_float(0.0,fmt)));
        }
        else
        {
            // Default precision was specified so don't make any assumptions
            // and use the format for double precision.
            return cmpf_from_cl_N(complex(x,cl_float(0.0,x)));
        }
    }
    else if (PyComplex_Check(v))
    {
        cl_N z;
        if (py_complex_to_cl_N(v, z) < 0)
        {
            PyErr_SetString(PyExc_ValueError, "cmpf: invalid complex");
            return NULL;
        }

        if (prec > 0)
        {
            // The user has specified a precision so honor that request.
            cl_F x = cl_float(realpart(z), fmt);
            cl_F y = cl_float(imagpart(z), fmt);
            return cmpf_from_cl_N(complex(x,y));
        }
        else
        {
            // Default precision was specified so don't make any assumptions
            // and use the format for double precision.
            return cmpf_from_cl_N(z);
        }
    }
    else if (mpf_check_type(v))
    {
        cl_F x = *((mpf_object *)v)->pob_val;
        if (prec > 0)
        {
            // The user has specified a precision so honor that request.
            return cmpf_from_cl_N(complex(cl_float(x,fmt),cl_float(0.0,fmt)));
        }
        else
        {
            // Default precision was specified so don't change anything.
            return cmpf_from_cl_N(complex(x,cl_float(0.0,x)));
        }
    }
    else if (mpq_check_type(v))
    {
        cl_RA q = *((mpq_object *)v)->pob_val;
        return cmpf_from_cl_N(complex(cl_float(q,fmt),cl_float(0.0,fmt)));
    }
    else if (cmpq_check_type(v))
    {
        cl_N z = *((cmpq_object *)v)->pob_val;
        cl_F x = cl_float(realpart(z), fmt);
        cl_F y = cl_float(imagpart(z), fmt);
        return cmpf_from_cl_N(complex(x,y));
    }

    PyErr_SetString(PyExc_TypeError, "cmpf: unknown type");
    return NULL;
}

//----------------------------------------------------------------------------
static PyObject *
string_to_cmpf(PyObject *v, int prec)
{
    float_format_t fmt = get_float_format_t(prec);

    // Call Python function to clean up the input string and handle errors.
    PyObject *result = PyObject_CallFunction(_cmpf_clean_str, "O", v);
    if (result == NULL)
        return NULL;

    // Set up the read flags to use the precision established by the user.
    cl_read_flags crf;
    crf.syntax = syntax_lfloat;
    crf.lsyntax = lsyntax_standard;
    crf.float_flags.default_float_format = fmt;
    crf.float_flags.default_lfloat_format = fmt;
    crf.float_flags.mantissa_dependent_float_format = cl_false;

    char const *s = PyString_AS_STRING(PyTuple_GET_ITEM(result,0));
    cl_F x = read_float(crf, s, NULL, NULL);

    s = PyString_AS_STRING(PyTuple_GET_ITEM(result,1));
    cl_F y = read_float(crf, s, NULL, NULL);

    Py_DECREF(result);

    return cmpf_from_cl_N(complex(x,y));
}

//----------------------------------------------------------------------------
static PyObject *
cmpf_add(PyObject *v, PyObject *w)
{
    cl_N a,b;
    CONVERT_TO_CL_N(v, a);
    CONVERT_TO_CL_N(w, b);
    a = a + b;
    return cmpf_from_cl_N(a);
}

//----------------------------------------------------------------------------
static PyObject *
cmpf_sub(PyObject *v, PyObject *w)
{
    cl_N a,b;
    CONVERT_TO_CL_N(v, a);
    CONVERT_TO_CL_N(w, b);
    a = a - b;
    return cmpf_from_cl_N(a);
}

//----------------------------------------------------------------------------
static PyObject *
cmpf_mul(PyObject *v, PyObject *w)
{
    cl_N a,b;
    CONVERT_TO_CL_N(v, a);
    CONVERT_TO_CL_N(w, b);
    a = a * b;

    // Note: the CLN library returns an exact type if an exact zero is used in
    // the calculation.  Need to make sure the conversion to float preserves
    // the precision of the floating point input.
    if ((a == 0) && (_check_exact(v) || _check_exact(w)))
    {
        // The result is zero and one of the operands is exact.
        cl_F f,z;
        if (cmpf_check_type(v))
        {
            f = cl_float(realpart(*((cmpf_object *)v)->pob_val));
            z = cl_float(0, f);
        }
        else if (cmpf_check_type(w))
        {
            f = cl_float(realpart(*((cmpf_object *)w)->pob_val));
            z = cl_float(0, f);
        }
        a = complex(z,z);
    }
    return cmpf_from_cl_N(a);
}

//----------------------------------------------------------------------------
static PyObject *
cmpf_div(PyObject *v, PyObject *w)
{
    cl_N a,b;
    CONVERT_TO_CL_N(v, a);
    CONVERT_TO_CL_N(w, b);
    if (b == 0.0) {
        PyErr_SetString(PyExc_ZeroDivisionError, "cmpf division");
        return NULL;
    }

    a = a / b;

    // Note: the CLN library returns an exact type if an exact zero is used in
    // the calculation.  Need to make sure the conversion to float preserves
    // the precision of the floating point input.
    if ((a == 0) && _check_exact(v))
    {
        // The result is zero and the first operand is exact.
        cl_F f = cl_float(realpart(*((cmpf_object *)w)->pob_val));
        cl_F z = cl_float(0, f);
        a = complex(z,z);
    }
    return cmpf_from_cl_N(a);
}

//----------------------------------------------------------------------------
static PyObject *
cmpf_pow(PyObject *px, PyObject *py, PyObject *pz)
{
    if (pz != Py_None)
    {
        PyErr_SetString(PyExc_TypeError, "pow() 3rd argument not "
            "allowed unless all arguments are integers");
        return NULL;
    }

    cl_N x, y;
    CONVERT_TO_CL_N(px, x);
    CONVERT_TO_CL_N(py, y);

    // There is a bug in CLN that is triggered when the first argument is an
    // exact number.  Explicitly transform to float in this case.  Note this
    // can only happen when the second argument is cmpf.
    if (PyInt_Check(px) | PyLong_Check(px) |
        mpq_check_type(px) | cmpq_check_type(px))
    {
        float_format_t fmt = float_format(cl_float(realpart(y)));

        cl_F a = cl_float(realpart(x), fmt);
        cl_F b = cl_float(imagpart(x), fmt);

        x = complex(a,b);
    }

    float_format_t fmt = float_format(cl_float(realpart(x)));

    // Sort out special cases here instead of relying on library.
    // This makes sure they are defined the way Python defines them.
    if (y == 0.0)
    {
        // x**0 is 1, even 0**0
        cl_N r = complex(cl_float(1.0,fmt), cl_float(0.0,fmt));
        return cmpf_from_cl_N(r);
    }

    if (x == 0.0)
    {
        if (realpart(y) < 0.0 || imagpart(y) != 0.0) {
            PyErr_SetString(PyExc_ZeroDivisionError,
                    "0.0 to a negative or complex power");
            return NULL;
        }
        cl_N r = complex(cl_float(0.0,fmt), cl_float(0.0,fmt));
        return cmpf_from_cl_N(r);
    }

    // Now we rely on CLN to get the math correct.

    return cmpf_from_cl_N(expt(x,y));
}

//----------------------------------------------------------------------------
static PyObject *
cmpf_neg(cmpf_object *v)
{
    return cmpf_from_cl_N( -(*v->pob_val));
}

//----------------------------------------------------------------------------
static PyObject *
cmpf_abs(cmpf_object *v)
{
    return mpf_from_cl_F(cl_float(abs(*v->pob_val)));
}

//----------------------------------------------------------------------------
// Adapted from the version in complexobject.c
static PyObject *
cmpf_richcompare(PyObject *v, PyObject *w, int op)
{
    if (op != Py_EQ && op != Py_NE)
    {
        PyErr_SetString(PyExc_TypeError,
            "cannot compare complex numbers using <, <=, >, >=");
        return NULL;
    }

    int c = PyNumber_CoerceEx(&v, &w);
    if (c < 0)
        return NULL;

    if (c > 0)
    {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    // Make sure both arguments are cmpf.
    if (!(cmpf_check_type(v) && cmpf_check_type(w)))
    {
        Py_DECREF(v);
        Py_DECREF(w);
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    cl_N a = *((cmpf_object *)v)->pob_val;
    cl_N b = *((cmpf_object *)w)->pob_val;
    Py_DECREF(v);
    Py_DECREF(w);

    PyObject *res;
    if ((a == b) == (op == Py_EQ))
        res = Py_True;
    else
        res = Py_False;

    Py_INCREF(res);
    return res;
}

//----------------------------------------------------------------------------
static int
cmpf_nonzero(cmpf_object *v)
{
    return !zerop(*v->pob_val);
}

//----------------------------------------------------------------------------
static int
cmpf_coerce(PyObject **pv, PyObject **pw)
{
    // This is the easy case, if the other type is also a cmpf the two types
    // are considered the same even if they have different precisions.  The
    // operations performed on these values will operate correctly because the
    // CLN library will handle them.
    if (cmpf_check_type(*pw))
    {
        Py_INCREF(*pv);
        Py_INCREF(*pw);
        return 0;
    }

    // Get the value of self.real so the format of the new object is the same.
    cl_F a = cl_float(realpart(*((cmpf_object *)(*pv))->pob_val));

    if (PyInt_Check(*pw))
    {
        cl_I z = PyInt_AS_LONG(*pw);
        *pw = cmpf_from_cl_N(complex(cl_float(z,a),cl_float(0.0,a)));
        Py_INCREF(*pv);
        return 0;
    }
    else if (PyLong_Check(*pw))
    {
        cl_I z = py_long_to_cl_I((PyLongObject *)(*pw));
        *pw = cmpf_from_cl_N(complex(cl_float(z,a),cl_float(0.0,a)));
        Py_INCREF(*pv);
        return 0;
    }
    else if (PyFloat_Check(*pw))
    {
        // This is an implicit conversion so use the double precision format.
        cl_F x;
        if (py_float_to_cl_F(*pw, x) < 0)
            return 1;

        *pw = cmpf_from_cl_N(complex(x,cl_float(0.0,x)));
        Py_INCREF(*pv);
        return 0;
    }
    else if (PyComplex_Check(*pw))
    {
        // This is an implicit conversion so use the double precision format.
        cl_N z;
        if (py_complex_to_cl_N(*pw, z) < 0)
            return 1;

        *pw = cmpf_from_cl_N(z);
        Py_INCREF(*pv);
        return 0;
    }
    else if (mpf_check_type(*pw))
    {
        cl_F x = *((mpf_object *)(*pw))->pob_val;
        *pw = cmpf_from_cl_N(complex(x,cl_float(0.0,x)));
        Py_INCREF(*pv);
        return 0;
    }
    else if (mpq_check_type(*pw))
    {
        cl_RA q = *((mpq_object *)(*pw))->pob_val;
        *pw = cmpf_from_cl_N(complex(cl_float(q,a),cl_float(0.0,a)));
        Py_INCREF(*pv);
        return 0;
    }
    else if (cmpq_check_type(*pw))
    {
        cl_N z = *((cmpq_object *)(*pw))->pob_val;
        cl_F x = cl_float(realpart(z), a);
        cl_F y = cl_float(imagpart(z), a);
        *pw = cmpf_from_cl_N(complex(x,y));
        Py_INCREF(*pv);
        return 0;
    }

    // Don't recognize the other type
    return 1;
}

//----------------------------------------------------------------------------
// Since we want cmpf numbers to be interoperable with Python numbers, should
// use the same hash algorithm as Python complex on a double approximation of
// the cmpf.

static long
cmpf_hash(cmpf_object *v)
{
    double real = double_approx(realpart(*v->pob_val));
    double imag = double_approx(imagpart(*v->pob_val));

    PyObject *ob = PyComplex_FromDoubles(real, imag);
    long result = PyObject_Hash(ob);
    Py_DECREF(ob);

    return result;
}

//----------------------------------------------------------------------------
static PyObject *
cmpf_repr(cmpf_object *v)
{
    cl_F real = cl_float(realpart(*v->pob_val));
    cl_F imag = cl_float(imagpart(*v->pob_val));

    // Force the use of the E notation so that the strings are compatible with
    // a Python float.
    print_flags.default_float_format = float_format(real);

    std::ostringstream out_stream;

    out_stream << "cmpf('";
    print_float(out_stream, print_flags, real);
    if (imag >= 0.0)
        out_stream << "+";
    print_float(out_stream, print_flags, imag);
    out_stream << "j',prec=";
    out_stream << mpf_prec_from_cl_F(real);
    out_stream << ")";

    std::string s = out_stream.str();
    std::size_t i = s.find('E');
    while (i != std::string::npos)
    {
        s[i] = 'e';
        i = s.find('E', i+1);
    }

    return PyString_FromString(s.c_str());
}

//----------------------------------------------------------------------------
static PyObject *
cmpf_str(cmpf_object *v)
{
    // Convert the value to a format that doesn't display all digits that are
    // possible.  This should make the results a bit more readable.  The user
    // can get full precision by using repr() instead of str().
    float_format_t fmt = float_format(mpf_str_prec);

    cl_F real = cl_float(realpart(*v->pob_val), fmt);
    cl_F imag = cl_float(imagpart(*v->pob_val), fmt);

    // Force the use of the E notation so that the strings are compatible with
    // a Python float.
    print_flags.default_float_format = fmt;

    std::ostringstream out_stream;

    out_stream << "(";
    print_float(out_stream, print_flags, real);
    if (imag >= 0.0)
        out_stream << "+";
    print_float(out_stream, print_flags, imag);
    out_stream << "j)";

    std::string s = out_stream.str();
    std::size_t i = s.find('E');
    while (i != std::string::npos)
    {
        s[i] = 'e';
        i = s.find('E', i+1);
    }

    return PyString_FromString(s.c_str());
}

//----------------------------------------------------------------------------
// Getter for cmpf precision.  Used for the prec attribute of cmpf objects.
static PyObject *
cmpf_getprec(cmpf_object *self, void *closure)
{
    cl_F real = cl_float(realpart(*self->pob_val));
    return PyInt_FromLong(mpf_prec_from_cl_F(real));
}

//----------------------------------------------------------------------------
// Getter for cmpf real part.  Used for the real attribute of cmpf objects.
static PyObject *
cmpf_getreal(cmpf_object *self, void *closure)
{
    cl_F real = cl_float(realpart(*self->pob_val));
    return mpf_from_cl_F(real);
}

//----------------------------------------------------------------------------
// Getter for cmpf imaginary part.  Used for the imag attribute of cmpf objects.
static PyObject *
cmpf_getimag(cmpf_object *self, void *closure)
{
    cl_F imag = cl_float(imagpart(*self->pob_val));
    return mpf_from_cl_F(imag);
}

//----------------------------------------------------------------------------
// Getter for cmpf phase.  Used for the phase attribute of cmpf objects.
static PyObject *
cmpf_getphase(cmpf_object *self, void *closure)
{
    cl_F p = cl_float(phase(*self->pob_val));
    return mpf_from_cl_F(p);
}

//----------------------------------------------------------------------------
static PyObject *
cmpf_complex(cmpf_object *self)
{
    double real = double_approx(realpart(*self->pob_val));
    double imag = double_approx(imagpart(*self->pob_val));

    return PyComplex_FromDoubles(real, imag);
}

//----------------------------------------------------------------------------
static PyObject *
cmpf_conjugate(cmpf_object *self)
{
    return cmpf_from_cl_N(conjugate(*self->pob_val));
}


//----------------------------------------------------------------------------
//*************** Complex rationals
//----------------------------------------------------------------------------

//----------------------------------------------------------------------------
// This routine handles checking for overflow conditions that can cause a CLF
// abort.  Also, applies the appropriate precision.
static int
py_complex_to_cl_NQ(PyObject *x, cl_N &y)
{
    double dr = PyComplex_RealAsDouble(x);
    double di = PyComplex_ImagAsDouble(x);

    if (Py_IS_INFINITY(dr) || Py_IS_INFINITY(di))
        return -1;

    // TODO - should handle NaNs here but have not done enough research to
    // detect them in a platform independent manner.  Doesn't seem to be
    // anything in Python header files that could help.  As a consequence, if
    // the user generates a NaN in Python, it will cause an abort in CLN.

    cl_RA real = rationalize(dr);
    cl_RA imag = rationalize(di);
    y = complex(real, imag);
    return 0;
}


//----------------------------------------------------------------------------
// The class library for numbers has its own memory management so we need to
// get a pointer to a CLN object and store it in the Python object.  This
// memory must also be released when the Python object is garbage collected.

static PyObject *
cmpq_from_cl_NQ(cl_N const &v)
{
    cmpq_object *newob = 0;

    if(!(newob = PyObject_New(cmpq_object, &cmpq_type)))
        return NULL;

    if (!(newob->pob_val = new cl_N))
    {
        Py_DECREF(newob);
        return PyErr_NoMemory();
    }

    *newob->pob_val = v;

    return (PyObject *)newob;
}

static void
cmpq_dealloc(cmpq_object *self)
{
    delete self->pob_val;
    self->ob_type->tp_free((PyObject *)self);
}

//----------------------------------------------------------------------------
static PyObject *
cmpq_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyObject *real = Py_False; // Integer zero, borrowed reference
    PyObject *imag = Py_None;  // Borrowed reference

    static char *kwlist[] = {"real", "imag", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OO:cmpf", kwlist,
                &real, &imag))
        return NULL;

    if (imag == Py_None)
    {
        if (PyString_Check(real) || PyUnicode_Check(real))
            return string_to_cmpq(real);

        return anynum_to_cmpq(real);
    }

    // At this point, both the real and imaginary parts must be some kind of
    // real values.  Coerce them to mpq type.

    mpq_object *ob = (mpq_object *)anyreal_to_mpq(real);
    if (ob == NULL)
        return NULL;

    cl_RA x = *ob->pob_val;
    Py_DECREF(ob);

    ob = (mpq_object *)anyreal_to_mpq(imag);
    if (ob == NULL)
        return NULL;

    cl_RA y = *ob->pob_val;
    Py_DECREF(ob);

    return cmpq_from_cl_NQ(complex(x,y));
}

//----------------------------------------------------------------------------
// Adapted from the routines in floatobject.c
//
// Note: This macro simply returns the value for cmpq objects.  Any other exact
// number is converted to cl_N using the appropriate data type.  Since the
// conversion is implicit, inexact types are excluded.

#define CONVERT_TO_CL_NQ(obj, cln) \
    if (cmpq_check_type(obj))     \
        cln = *((cmpq_object *)obj)->pob_val; \
    else if (cmpq_convert_to_cl_NQ(&(obj), &(cln)) < 0) \
        return obj;

static int
cmpq_convert_to_cl_NQ(PyObject **v, cl_N *cln)
{
    PyObject *obj = *v;

    if (PyInt_Check(obj))
    {
        cl_I z = PyInt_AS_LONG(obj);
        *cln = z;
    }
    else if (PyLong_Check(obj))
    {
        cl_I z = py_long_to_cl_I((PyLongObject *)obj);
        *cln = z;
    }
    else if (mpq_check_type(obj))
    {
        cl_RA q = *((mpq_object *)obj)->pob_val;
        *cln = q;
    }
    else
    {
        Py_INCREF(Py_NotImplemented);
        *v = Py_NotImplemented;
        return -1;
    }
    return 0;
}

//----------------------------------------------------------------------------
static PyObject *
anynum_to_cmpq(PyObject *v)
{
    if (cmpq_check_type(v))
    {
        Py_INCREF(v);
        return v;
    }

    if (PyInt_Check(v))
    {
        cl_I ix = PyInt_AS_LONG(v);
        return cmpq_from_cl_NQ(ix);
    }
    else if (PyLong_Check(v))
    {
        cl_I ix = py_long_to_cl_I((PyLongObject *)v);
        return cmpq_from_cl_NQ(ix);
    }
    else if (PyFloat_Check(v))
    {
        cl_F x;
        if (py_float_to_cl_F(v, x) < 0)
        {
            PyErr_SetString(PyExc_ValueError, "cmpq: invalid float");
            return NULL;
        }

        return cmpq_from_cl_NQ(rationalize(x));
    }
    else if (PyComplex_Check(v))
    {
        cl_N z;
        if (py_complex_to_cl_NQ(v, z) < 0)
        {
            PyErr_SetString(PyExc_ValueError, "cmpq: invalid complex");
            return NULL;
        }

        return cmpq_from_cl_NQ(z);
    }
    else if (mpf_check_type(v))
    {
        cl_RA x = rationalize(*((mpf_object *)v)->pob_val);
        return cmpq_from_cl_NQ(x);
    }
    else if (mpq_check_type(v))
    {
        cl_RA q = *((mpq_object *)v)->pob_val;
        return cmpq_from_cl_NQ(q);
    }
    else if (cmpf_check_type(v))
    {
        cl_N z = *((cmpf_object *)v)->pob_val;
        cl_RA x = rationalize(realpart(z));
        cl_RA y = rationalize(imagpart(z));
        return cmpq_from_cl_NQ(complex(x,y));
    }

    PyErr_SetString(PyExc_TypeError, "cmpq: unknown type");
    return NULL;
}

//----------------------------------------------------------------------------
static PyObject *
string_to_cmpq(PyObject *v)
{
    // Call Python function to clean up the input string and handle errors.
    PyObject *result = PyObject_CallFunction(_cmpq_clean_str, "O", v);
    if (result == NULL)
        return NULL;

    cl_read_flags crf;
    crf.syntax = syntax_rational;
    crf.lsyntax = lsyntax_standard;
    crf.rational_base = 10;

    char const *s = PyString_AS_STRING(PyTuple_GET_ITEM(result,0));
    cl_RA x = read_rational(crf, s, NULL, NULL);

    s = PyString_AS_STRING(PyTuple_GET_ITEM(result,1));
    cl_RA y = read_rational(crf, s, NULL, NULL);

    Py_DECREF(result);

    return cmpq_from_cl_NQ(complex(x,y));
}

//----------------------------------------------------------------------------
static PyObject *
cmpq_add(PyObject *v, PyObject *w)
{
    cl_N a,b;
    CONVERT_TO_CL_NQ(v, a);
    CONVERT_TO_CL_NQ(w, b);
    a = a + b;
    return cmpq_from_cl_NQ(a);
}

//----------------------------------------------------------------------------
static PyObject *
cmpq_sub(PyObject *v, PyObject *w)
{
    cl_N a,b;
    CONVERT_TO_CL_NQ(v, a);
    CONVERT_TO_CL_NQ(w, b);
    a = a - b;
    return cmpq_from_cl_NQ(a);
}

//----------------------------------------------------------------------------
static PyObject *
cmpq_mul(PyObject *v, PyObject *w)
{
    cl_N a,b;
    CONVERT_TO_CL_NQ(v, a);
    CONVERT_TO_CL_NQ(w, b);
    a = a * b;
    return cmpq_from_cl_NQ(a);
}

//----------------------------------------------------------------------------
static PyObject *
cmpq_div(PyObject *v, PyObject *w)
{
    cl_N a,b;
    CONVERT_TO_CL_NQ(v, a);
    CONVERT_TO_CL_NQ(w, b);
    if (b == 0.0) {
        PyErr_SetString(PyExc_ZeroDivisionError, "cmpq division");
        return NULL;
    }

    a = a / b;
    return cmpq_from_cl_NQ(a);
}

//----------------------------------------------------------------------------
static PyObject *
cmpq_pow(PyObject *px, PyObject *py, PyObject *pz)
{
    if (pz != Py_None)
    {
        PyErr_SetString(PyExc_TypeError, "pow() 3rd argument not "
            "allowed unless all arguments are integers");
        return NULL;
    }

    cl_N x;
    CONVERT_TO_CL_NQ(px, x);
    cl_RA y;
    CONVERT_TO_CL_RA(py, y);

    // Sort out special cases here instead of relying on library.
    // This makes sure they are defined the way Python defines them.
    if (y == 0)
    {
        // x**0 is 1, even 0**0
        return cmpq_from_cl_NQ((cl_RA)1);
    }

    if (x == 0.0)
    {
        if (y < 0)
        {
            PyErr_SetString(PyExc_ZeroDivisionError,
                    "0 to a negative power");
            return NULL;
        }
        return cmpq_from_cl_NQ((cl_RA)0);
    }

    if (denominator(y) != 1)
    {
        PyErr_SetString(PyExc_ValueError, "pow(x,y) y must be an integer");
        return NULL;
    }

    // Now we rely on CLN to get the math correct.
    return cmpq_from_cl_NQ(expt(x,numerator(y)));
}

//----------------------------------------------------------------------------
static PyObject *
cmpq_neg(cmpq_object *v)
{
    return cmpq_from_cl_NQ( -(*v->pob_val));
}

//----------------------------------------------------------------------------
// Adapted from the version in complexobject.c
static PyObject *
cmpq_richcompare(PyObject *v, PyObject *w, int op)
{
    if (op != Py_EQ && op != Py_NE)
    {
        PyErr_SetString(PyExc_TypeError,
            "cannot compare complex numbers using <, <=, >, >=");
        return NULL;
    }

    int c = PyNumber_CoerceEx(&v, &w);
    if (c < 0)
        return NULL;

    if (c > 0)
    {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    // Make sure both arguments are cmpq.
    if (!(cmpq_check_type(v) && cmpq_check_type(w)))
    {
        Py_DECREF(v);
        Py_DECREF(w);
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    cl_N a = *((cmpq_object *)v)->pob_val;
    cl_N b = *((cmpq_object *)w)->pob_val;
    Py_DECREF(v);
    Py_DECREF(w);

    PyObject *res;
    if ((a == b) == (op == Py_EQ))
        res = Py_True;
    else
        res = Py_False;

    Py_INCREF(res);
    return res;
}

//----------------------------------------------------------------------------
static int
cmpq_nonzero(cmpq_object *v)
{
    return !zerop(*v->pob_val);
}

//----------------------------------------------------------------------------
static int
cmpq_coerce(PyObject **pv, PyObject **pw)
{
    if (cmpq_check_type(*pw))
    {
        Py_INCREF(*pv);
        Py_INCREF(*pw);
        return 0;
    }

    if (PyInt_Check(*pw))
    {
        cl_I z = PyInt_AS_LONG(*pw);
        *pw = cmpq_from_cl_NQ(z);
        Py_INCREF(*pv);
        return 0;
    }
    else if (PyLong_Check(*pw))
    {
        cl_I z = py_long_to_cl_I((PyLongObject *)(*pw));
        *pw = cmpq_from_cl_NQ(z);
        Py_INCREF(*pv);
        return 0;
    }
    else if (mpq_check_type(*pw))
    {
        cl_RA q = *((mpq_object *)(*pw))->pob_val;
        *pw = cmpq_from_cl_NQ(q);
        Py_INCREF(*pv);
        return 0;
    }

    // Don't recognize the other type
    return 1;
}

//----------------------------------------------------------------------------
// Since we want cmpf numbers to be interoperable with Python numbers, should
// use the same hash algorithm as Python complex on a double approximation of
// the cmpq.

static long
cmpq_hash(cmpq_object *v)
{
    double real = double_approx(realpart(*v->pob_val));
    double imag = double_approx(imagpart(*v->pob_val));

    PyObject *ob = PyComplex_FromDoubles(real, imag);
    long result = PyObject_Hash(ob);
    Py_DECREF(ob);

    return result;
}

//----------------------------------------------------------------------------
static PyObject *
cmpq_repr(cmpq_object *v)
{
    cl_RA real = rationalize(realpart(*v->pob_val));
    cl_RA imag = rationalize(imagpart(*v->pob_val));

    std::ostringstream out_stream;

    out_stream << "cmpq('";
    print_rational(out_stream, print_flags, real);
    if (imag >= 0)
        out_stream << "+";
    print_rational(out_stream, print_flags, imag);
    out_stream << "j')";

    return PyString_FromString(out_stream.str().c_str());
}

//----------------------------------------------------------------------------
static PyObject *
cmpq_str(cmpq_object *v)
{
    cl_RA real = rationalize(realpart(*v->pob_val));
    cl_RA imag = rationalize(imagpart(*v->pob_val));

    std::ostringstream out_stream;

    out_stream << "(";
    print_rational(out_stream, print_flags, real);
    if (imag >= 0)
        out_stream << "+";
    print_rational(out_stream, print_flags, imag);
    out_stream << "j)";

    return PyString_FromString(out_stream.str().c_str());
}

//----------------------------------------------------------------------------
// Getter for cmpq real part.  Used for the real attribute of cmpq objects.
static PyObject *
cmpq_getreal(cmpq_object *self, void *closure)
{
    cl_RA real = rationalize(realpart(*self->pob_val));
    return mpq_from_cl_RA(real);
}

//----------------------------------------------------------------------------
// Getter for cmpq imaginary part.  Used for the imag attribute of cmpq objects.
static PyObject *
cmpq_getimag(cmpq_object *self, void *closure)
{
    cl_RA imag = rationalize(imagpart(*self->pob_val));
    return mpq_from_cl_RA(imag);
}

//----------------------------------------------------------------------------
static PyObject *
cmpq_complex(cmpq_object *self)
{
    double real = double_approx(realpart(*self->pob_val));
    double imag = double_approx(imagpart(*self->pob_val));

    return PyComplex_FromDoubles(real, imag);
}

//----------------------------------------------------------------------------
static PyObject *
cmpq_conjugate(cmpq_object *self)
{
    return cmpq_from_cl_NQ(conjugate(*self->pob_val));
}

//****************************************************************************
//----------------------------------------------------------------------------
// ***** Module level functions
//----------------------------------------------------------------------------
//****************************************************************************
// NOTE: All of these functions can operate on any type number.  If the input
// is a real type, the result is an mpf or an exception.  Otherwise, the result
// is a cmpf or an exception.
//
// To avoid user confusion, numbers are not automatically promoted to complex.

//----------------------------------------------------------------------------
static int
anyreal_to_cl_F(PyObject *ob, cl_F &x)
{
    mpf_object *px = (mpf_object *)anyreal_to_mpf(ob, 0);
    if (px == NULL)
    {
        // Cancel the error and return failure.
        PyErr_Clear();
        return -1;
    }

    x = *px->pob_val;
    Py_DECREF(px);
    return 0;
}

//----------------------------------------------------------------------------
static int
anynum_to_cl_N(PyObject *ob, cl_N &z)
{
    cmpf_object *pz = (cmpf_object *)anynum_to_cmpf(ob, 0);
    if (pz == NULL)
    {
        // Cancel the error and return failure.
        PyErr_Clear();
        return -1;
    }

    z = *pz->pob_val;
    Py_DECREF(pz);
    return 0;
}

//----------------------------------------------------------------------------
static PyObject *
all_exp1(PyObject *self, PyObject *args, PyObject *kwds)
{
    int prec = 0;
    static char *kwlist[] = {"prec", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|i:exp1", kwlist, &prec))
        return NULL;

    return mpf_from_cl_F(exp1(get_float_format_t(prec)));
}

//----------------------------------------------------------------------------
static PyObject *
all_pi(PyObject *self, PyObject *args, PyObject *kwds)
{
    int prec = 0;
    static char *kwlist[] = {"prec", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|i:pi", kwlist, &prec))
        return NULL;

    return mpf_from_cl_F(pi(get_float_format_t(prec)));
}

//----------------------------------------------------------------------------
static PyObject *
all_sqrt(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:sqrt", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        if (x < 0.0)
        {
            PyErr_SetString(PyExc_ValueError, "sqrt of negative number");
            return NULL;
        }
        return mpf_from_cl_F(sqrt(x));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "sqrt: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(sqrt(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_exp(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:exp", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        return mpf_from_cl_F(cl_float(exp(x)));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "exp: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(exp(z));
}

//----------------------------------------------------------------------------
// Helper function for the log default case.
static PyObject *
_all_log(PyObject *px)
{
    cl_F x;
    if (anyreal_to_cl_F(px, x) == 0)
    {
        if (x <= 0.0)
        {
            PyErr_SetString(PyExc_ValueError, "log domain error");
            return NULL;
        }
        return mpf_from_cl_F(cl_float(ln(x)));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(px, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "log: unknown type");
        return NULL;
    }

    if (z == 0.0)
    {
        PyErr_SetString(PyExc_ValueError, "log of zero");
        return NULL;
    }

    return cmpf_from_cl_N(log(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_log(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *px;
    PyObject *pb = NULL;

    static char *kwlist[] = {"x", "b", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O:log", kwlist, &px, &pb))
        return NULL;

    // First dispose of the default case.
    if (pb == NULL)
        return _all_log(px);

    // Now the user has supplied both parameters.
    cl_F x, b;
    if (anyreal_to_cl_F(px, x) == 0 && anyreal_to_cl_F(pb, b) == 0)
    {
        if (x <= 0.0 || b <= 0.0)
        {
            PyErr_SetString(PyExc_ValueError, "log domain error");
            return NULL;
        }
        return mpf_from_cl_F(cl_float(log(x,b)));
    }

    // Retry as complex numbers.

    cl_N cx, cb;
    if (anynum_to_cl_N(px, cx) < 0 || anynum_to_cl_N(pb, cb) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "log: unknown type");
        return NULL;
    }

    if (cx == 0.0 || cb == 0.0)
    {
        PyErr_SetString(PyExc_ValueError, "log of zero");
        return NULL;
    }

    return cmpf_from_cl_N(log(cx,cb));
}

//----------------------------------------------------------------------------
static PyObject *
all_log10(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:log10", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        if (x <= 0.0)
        {
            PyErr_SetString(PyExc_ValueError, "log domain error");
            return NULL;
        }
        return mpf_from_cl_F(cl_float(log(x,10)));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "log10: unknown type");
        return NULL;
    }

    if (z == 0.0)
    {
        PyErr_SetString(PyExc_ValueError, "log of zero");
        return NULL;
    }

    return cmpf_from_cl_N(log(z,10));
}

//----------------------------------------------------------------------------
static PyObject *
all_cos(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:cos", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        return mpf_from_cl_F(cl_float(cos(x)));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "cos: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(cos(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_sin(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:sin", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        return mpf_from_cl_F(cl_float(sin(x)));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "sin: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(sin(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_tan(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:tan", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        return mpf_from_cl_F(cl_float(tan(x)));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "tan: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(tan(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_degrees(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:degrees", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        return mpf_from_cl_F(x*cl_float(180,x)/pi(x));
    }

    // While this function could be extended to the complex numbers, it is only
    // in the Python math library.  Extending it would probably be confusing.
    PyErr_SetString(PyExc_TypeError, "degrees: unknown type");
    return NULL;
}

//----------------------------------------------------------------------------
static PyObject *
all_radians(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:radians", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        return mpf_from_cl_F(x*pi(x)/cl_float(180,x));
    }

    // While this function could be extended to the complex numbers, it is only
    // in the Python math library.  Extending it would probably be confusing.
    PyErr_SetString(PyExc_TypeError, "radians: unknown type");
    return NULL;
}

//----------------------------------------------------------------------------
static PyObject *
all_acos(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:acos", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        if (x < -1.0 || x > 1.0)
        {
            PyErr_SetString(PyExc_ValueError, "acos domain error");
            return NULL;
        }
        return mpf_from_cl_F(cl_float(realpart(acos(x))));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "acos: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(acos(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_asin(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:asin", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        if (x < -1.0 || x > 1.0)
        {
            PyErr_SetString(PyExc_ValueError, "asin domain error");
            return NULL;
        }
        return mpf_from_cl_F(cl_float(realpart(asin(x))));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "asin: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(asin(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_atan(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:atan", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        return mpf_from_cl_F(cl_float(atan(x)));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "atan: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(atan(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_atan2(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *px;
    PyObject *py;

    static char *kwlist[] = {"y", "x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO:atan2", kwlist, &py, &px))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(px, x) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "atan2: unknown type for x");
        return NULL;
    }

    cl_F y;
    if (anyreal_to_cl_F(py, y) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "atan2: unknown type for y");
        return NULL;
    }

    return mpf_from_cl_F(cl_float(atan(x,y)));
}

//----------------------------------------------------------------------------
static PyObject *
all_cis(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"z", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:cis", kwlist, &ob))
        return NULL;

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "cis: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(cis(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_cosh(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:cosh", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        return mpf_from_cl_F(cl_float(cosh(x)));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "cosh: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(cosh(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_sinh(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:sinh", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        return mpf_from_cl_F(cl_float(sinh(x)));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "sinh: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(sinh(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_tanh(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:tanh", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) == 0)
    {
        return mpf_from_cl_F(cl_float(tanh(x)));
    }

    // Retry as a complex number.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "tanh: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(tanh(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_acosh(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:acosh", kwlist, &ob))
        return NULL;

    // This function only supports complex numbers.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "acosh: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(acosh(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_asinh(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:asinh", kwlist, &ob))
        return NULL;

    // This function only supports complex numbers.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "asinh: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(asinh(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_atanh(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:atanh", kwlist, &ob))
        return NULL;

    // This function only supports complex numbers.

    cl_N z;
    if (anynum_to_cl_N(ob, z) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "atanh: unknown type");
        return NULL;
    }

    return cmpf_from_cl_N(atanh(z));
}

//----------------------------------------------------------------------------
static PyObject *
all_round(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;
    long n = 0;

    static char *kwlist[] = {"x", "n", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|l:round", kwlist, &ob, &n))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "round: unknown type");
        return NULL;
    }

    // Want the behavior of round to match the Python built-in function.

    int sn = 1;
    if (n < 0)
    {
        n = -n;
        sn = -1;
    }

    cl_F sx = cl_float(1.0,x);
    if (x < 0.0)
    {
        x = -x;
        sx = cl_float(-1.0,x);
    }

    cl_F s = cl_float(1.0, x);
    if (n > 0)
        s = cl_float(expt_pos((cl_I)10,(cl_I)n), x);

    if (sn < 0)
        x = x/s;
    else
        x = x*s;

    cl_F_div_t r = floor2(x);

    x = cl_float(r.quotient, x);
    if (r.remainder >= 0.5)
        x = x + 1;

    if (sn < 0)
        x = sx*x*s;
    else
        x = sx*x/s;

    return mpf_from_cl_F(x);
}

//----------------------------------------------------------------------------
static PyObject *
all_floor(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:floor", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "floor: unknown type");
        return NULL;
    }

    return mpf_from_cl_F(ffloor(x));
}

//----------------------------------------------------------------------------
static PyObject *
all_ceil(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:ceil", kwlist, &ob))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(ob, x) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "ceil: unknown type");
        return NULL;
    }

    return mpf_from_cl_F(fceiling(x));
}

//----------------------------------------------------------------------------
static PyObject *
all_hypot(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *px;
    PyObject *py;

    static char *kwlist[] = {"x", "y", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO:hypot", kwlist, &px, &py))
        return NULL;

    cl_F x;
    if (anyreal_to_cl_F(px, x) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "hypot: unknown type for x");
        return NULL;
    }

    cl_F y;
    if (anyreal_to_cl_F(py, y) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "hypot: unknown type for y");
        return NULL;
    }

    cl_F r;
    x = abs(x);
    y = abs(y);

    if (x < y)
    {
        r = x/y;
        r = y*sqrt(1 + r*r);
    }
    else
    {
        if (x == 0.0)
        {
            // Both x and y are zero.  Add them to get the precision set
            // correctly.
            r = x+y;
        }
        else
        {
            r = y/x;
            r = x*sqrt(1 + r*r);
        }
    }

    return mpf_from_cl_F(r);
}

//----------------------------------------------------------------------------
static PyObject *
all_isreal(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:isreal", kwlist, &ob))
        return NULL;

    PyObject *result = Py_False;
    if (PyInt_Check(ob) | PyLong_Check(ob) | PyFloat_Check(ob) |
        mpq_check_type(ob) | mpf_check_type(ob))
    {
        result = Py_True;
    }

    Py_INCREF(result);
    return result;
}

//----------------------------------------------------------------------------
static PyObject *
all_iscomplex(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:iscomplex", kwlist, &ob))
        return NULL;

    PyObject *result = Py_False;
    if (PyComplex_Check(ob) | cmpq_check_type(ob) | cmpf_check_type(ob))
    {
        result = Py_True;
    }

    Py_INCREF(result);
    return result;
}

//----------------------------------------------------------------------------
static PyObject *
all_isexact(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *ob;

    static char *kwlist[] = {"x", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:isexact", kwlist, &ob))
        return NULL;

    PyObject *result = Py_False;
    if (_check_exact(ob))
    {
        result = Py_True;
    }

    Py_INCREF(result);
    return result;
}

//----------------------------------------------------------------------------
static PyObject *
all_factorial(PyObject *self, PyObject *args, PyObject *kwds)
{
    int n;

    static char *kwlist[] = {"n", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "i:factorial", kwlist, &n))
        return NULL;

    if (n < 0)
    {
        PyErr_SetString(PyExc_ValueError, "factorial: n < 0");
        return NULL;
    }

    // The ideal return value from this function should be an integer.
    // However, very large Python longs are much less efficient than mpq and
    // this module does not yet support CLN integers.
    return mpq_from_cl_RA(factorial((uintL)n));
}

//----------------------------------------------------------------------------
static PyObject *
all_doublefactorial(PyObject *self, PyObject *args, PyObject *kwds)
{
    int n;

    static char *kwlist[] = {"n", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "i:doublefactorial", kwlist, &n))
        return NULL;

    if (n < 0)
    {
        PyErr_SetString(PyExc_ValueError, "doublefactorial: n < 0");
        return NULL;
    }

    // The ideal return value from this function should be an integer.
    // However, very large Python longs are much less efficient than mpq and
    // this module does not yet support CLN integers.
    return mpq_from_cl_RA(doublefactorial((uintL)n));
}

//----------------------------------------------------------------------------
static PyObject *
all_binomial(PyObject *self, PyObject *args, PyObject *kwds)
{
    int n,m;

    static char *kwlist[] = {"m", "n", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ii:binomial", kwlist, &m, &n))
        return NULL;

    if (n < 0)
    {
        PyErr_SetString(PyExc_ValueError, "binomial: n < 0");
        return NULL;
    }

    if (m < 0)
    {
        PyErr_SetString(PyExc_ValueError, "binomial: m < 0");
        return NULL;
    }

    // The ideal return value from this function should be an integer.
    // However, very large Python longs are much less efficient than mpq and
    // this module does not yet support CLN integers.
    return mpq_from_cl_RA(binomial((uintL)m, (uintL)n));
}

//----------------------------------------------------------------------------
// ***************** Start Root Finder **********************
//----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// Copyright (c) 2004 Jack W. Crenshaw
// Permission to modify and release under the GPL obtained 2005.
// Modifications made by Raymond L. Buvel include replacing doubles with Class
// Library for Numbers floats and interfacing to Python.
//
// The original code was extracted from The World's Best Root Finder (TWBRF).
// http://www.embedded.com/columns/pt
//-----------------------------------------------------------------------------

// The TWBRF test function
// double f(double x){
//     return(4*sin(x)+exp(-x/6));
// }
// cout << iterate(f, 0, 6, 1.0e-8, 40) << endl;

//-----------------------------------------------------------------------------
// This function evaluates a new point, sets the y range,
// and tests for convergence

static int // Returns 0 for success -1 for exception
fr_get_y(cl_F x, PyObject *func, cl_F eps,
         cl_F &ymax, cl_F &ymin, bool &converged, cl_F &y)
{
    // Call Python function and return -1 on error.
    PyObject *arglist = PyTuple_New(1);
    PyTuple_SET_ITEM(arglist, 0, mpf_from_cl_F(x));
    PyObject *result = PyEval_CallObject(func, arglist);
    Py_DECREF(arglist);
    if (result == NULL)
        return -1;

    // The user may return any type of number so we need to convert it to a
    // cl_F and check for errors.
    if (anyreal_to_cl_F(result, y) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "find_root: unknown type for y");
        Py_DECREF(result);
        return -1;
    }

    Py_DECREF(result);

    ymax = max(ymax, y);
    ymin = min(ymin, y);
    converged = (abs(y) < eps*(ymax-ymin));
    return 0;
}

//-----------------------------------------------------------------------------
// The iterator
// Based upon the old IBM subroutine rtmi.for
// It uses alternating bisection and inverse
// parabolic interpolation
// restructured by Jack Crenshaw 03/2004
// Modified by Ray Buvel 07/2005

static int // Returns 0 for success -1 for exception
fr_iterate(PyObject *func, cl_F x1, cl_F x3, cl_F eps,
        int imax, cl_F &result)
{
    cl_F x2, y2;                  // the middle point in bisections
    cl_F xm, ym;                  // the estimated root in interpolations
    cl_F epsx = eps*abs(x3-x1);   // convergence criterion in x
    cl_F ymin = 1.0e-300;         // set up for criterion in y
    cl_F ymax = -ymin;
    bool converged = false;

    // evaluate function at limits
    cl_F y1;
    if (fr_get_y(x1, func, eps, ymax, ymin, converged, y1) < 0)
        return -1;

    if (y1 == 0.0)
    {
        // only exact zero accepted here
        result = x1;
        return 0;
    }

    cl_F y3;
    if (fr_get_y(x3, func, eps, ymax, ymin, converged, y3) < 0)
        return -1;

    if (y3 == 0.0)
    {
        // and here
        result = x3;
        return 0;
    }

    // initial points must straddle root
    if (y1 * y3 > 0.0)
    {
        PyErr_SetString(PyExc_RuntimeError,
                "find_root: Initial bounds do not straddle root");
        return -1;
    }

    // begin main bisection loop
    for (int i=0; i<imax; ++i)
    {
        x2 = (x1+x3)/2;     // bisect x range
        if (abs(x3 - x1) < epsx)
        {
            // If we're bisecting, we stop when the interval gets small
            result = x2;
            return 0;
        }
        if (fr_get_y(x2, func, eps, ymax, ymin, converged, y2) < 0)
            return -1;

        // perhaps we nailed the root?
        if (converged)
        {
            result = x2;
            return 0;
        }

        // relabel points to keep root between x1 and x2
        if (y1*y2 > 0.0)
        {
            cl_F tmp = x1;
            x1 = x3;
            x3 = tmp;
            tmp = y1;
            y1 = y3;
            y3 = tmp;
        }

        // here's where we try parabolic interpolation.
        // there are two criteria for accepting the point.
        // if any one of them fails, just bisect again.

        // note that y21 and y31 cannot be zero here
        // but y32 might be.
        cl_F y21=y2-y1;
        cl_F y32=y3-y2;
        if(y32 != 0.0)
        {
            cl_F y31=y3-y1;
            cl_F b=(x2-x1)/y21;
            cl_F c=(y21-y32)/(y32*y31);

            // Test for the RTMI condition
            if(y3*y31 >= 2*y2*y21)
            {
                xm=x1-b*y1*(1-c*y2);
                if (fr_get_y(xm, func, eps, ymax, ymin, converged, ym) < 0)
                    return -1;

                // perhaps we nailed the root?
                if(converged)
                {
                    result = xm;
                    return 0;
                }
                // Relabel the points as needed
                // to keep root between x1 and x2
                if(ym*y1 < 0.0)
                {
                    x2=xm;
                    y2=ym;
                }
                else
                {
                    x1=xm;
                    y1=ym;
                }
            }
        }
        // we didn't do parabolic interpolation.
        // just relabel points and continue.
        x3 = x2;
        y3 = y2;
    }
    // end of bisection loop. If we get here, we did not converge.
    // TODO record some diagnostic information for the exception.
    PyErr_SetString(PyExc_RuntimeError,
            "Iterate: Failed to converge in imax tries.");
    return -1;
}

//-----------------------------------------------------------------------------
static PyObject *
all_find_root(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *pfunc;
    PyObject *px1;
    PyObject *px3;
    PyObject *peps = NULL;
    int imax = 40;

    static char *kwlist[] = {"func", "x1", "x3", "eps", "imax", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOO|Oi:find_root", kwlist,
                &pfunc, &px1, &px3, &peps, &imax))
        return NULL;

    cl_F eps;
    if (peps == NULL)
    {
        eps = cl_float(1e-12, mpf_prec);
    }
    else
    {
        if (anyreal_to_cl_F(peps, eps) < 0)
        {
            PyErr_SetString(PyExc_TypeError, "find_root: unknown type for eps");
            return NULL;
        }
    }

    cl_F x1;
    if (anyreal_to_cl_F(px1, x1) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "find_root: unknown type for x1");
        return NULL;
    }

    cl_F x3;
    if (anyreal_to_cl_F(px3, x3) < 0)
    {
        PyErr_SetString(PyExc_TypeError, "find_root: unknown type for x3");
        return NULL;
    }

    cl_F x;
    if (fr_iterate(pfunc, x1, x3, eps, imax, x) < 0)
        return NULL;

    return mpf_from_cl_F(x);
}
//----------------------------------------------------------------------------
// ***************** End Root Finder **********************
//----------------------------------------------------------------------------

//----------------------------------------------------------------------------
//----------------------------------------------------------------------------
#define _WITH_KWDS (METH_VARARGS | METH_KEYWORDS)

static PyMethodDef clnum_methods[] = {
    {"get_default_precision", get_default_precision, METH_NOARGS,
        "get number of decimal digits in default precision"},
    {"set_default_precision", set_default_precision, METH_VARARGS,
        "set number of decimal digits in default precision"},
    {"exp1", (PyCFunction)all_exp1, _WITH_KWDS,
        "base of the natural logarithms with specified precision"},
    {"pi", (PyCFunction)all_pi, _WITH_KWDS,
        "pi with specified precision"},
    {"sqrt", (PyCFunction)all_sqrt, _WITH_KWDS,
        "square root"},
    {"exp", (PyCFunction)all_exp, _WITH_KWDS,
        "exponential"},
    {"log10", (PyCFunction)all_log10, _WITH_KWDS,
        "log to base ten"},
    {"log", (PyCFunction)all_log, _WITH_KWDS,
        "log(x[,b]) log of x to base b; defaults to natural log"},
    {"cos", (PyCFunction)all_cos, _WITH_KWDS,
        "cosine"},
    {"sin", (PyCFunction)all_sin, _WITH_KWDS,
        "sine"},
    {"tan", (PyCFunction)all_tan, _WITH_KWDS,
        "tangent"},
    {"degrees", (PyCFunction)all_degrees, _WITH_KWDS,
        "convert radians to degrees"},
    {"radians", (PyCFunction)all_radians, _WITH_KWDS,
        "convert degrees to radians"},
    {"acos", (PyCFunction)all_acos, _WITH_KWDS,
        "inverse cosine"},
    {"asin", (PyCFunction)all_asin, _WITH_KWDS,
        "inverse sine"},
    {"atan", (PyCFunction)all_atan, _WITH_KWDS,
        "inverse tangent"},
    {"atan2", (PyCFunction)all_atan2, _WITH_KWDS,
        "atan2(y,x) inverse tangent of y/x"},
    {"cis", (PyCFunction)all_cis, _WITH_KWDS,
        "cis(z) = cos(z) + j*sin(z)"},
    {"cosh", (PyCFunction)all_cosh, _WITH_KWDS,
        "hyperbolic cosine"},
    {"sinh", (PyCFunction)all_sinh, _WITH_KWDS,
        "hyperbolic sine"},
    {"tanh", (PyCFunction)all_tanh, _WITH_KWDS,
        "hyperbolic tangent"},
    {"acosh", (PyCFunction)all_acosh, _WITH_KWDS,
        "inverse hyperbolic cosine"},
    {"asinh", (PyCFunction)all_asinh, _WITH_KWDS,
        "inverse hyperbolic sine"},
    {"atanh", (PyCFunction)all_atanh, _WITH_KWDS,
        "inverse hyperbolic tangent"},
    {"round", (PyCFunction)all_round, _WITH_KWDS,
        "round(x[,n]) round x to n digits after decimal point (default n=0)"},
    {"floor", (PyCFunction)all_floor, _WITH_KWDS,
        "largest integer less than or equal to x"},
    {"ceil", (PyCFunction)all_ceil, _WITH_KWDS,
        "smallest integer greater than or equal to x"},
    {"hypot", (PyCFunction)all_hypot, _WITH_KWDS,
        "hypot(x,y) = sqrt(x*x + y*y)"},
    {"isreal", (PyCFunction)all_isreal, _WITH_KWDS,
        "isreal(x) True if x is a real number, False otherwise."},
    {"iscomplex", (PyCFunction)all_iscomplex, _WITH_KWDS,
        "iscomplex(x) True if x is a complex number, False otherwise."},
    {"isexact", (PyCFunction)all_isexact, _WITH_KWDS,
        "isexact(x) True if x is an exact number, False otherwise."},
    {"factorial", (PyCFunction)all_factorial, _WITH_KWDS,
        "factorial(n) n!"},
    {"doublefactorial", (PyCFunction)all_doublefactorial, _WITH_KWDS,
        "doublefactorial(n) n!!"},
    {"binomial", (PyCFunction)all_binomial, _WITH_KWDS,
        "binomial(m,n) binomial coefficient m!/n!(m-n)!"},
    {"find_root", (PyCFunction)all_find_root, _WITH_KWDS,
        "find_root(func,x1,x3[,eps,imax])"},
    {NULL}  /* Sentinel */
};

//----------------------------------------------------------------------------
PyMODINIT_FUNC
initclnum(void)
{
    // Initialize format settings
    mpf_prec = float_format(20);
    mpf_prec_for_double = float_format(mpf_min_prec);

    print_flags.rational_base = 10;
    print_flags.rational_readably = cl_false;
    print_flags.float_readably = cl_false;
    print_flags.complex_readably = cl_false;

    // Set the underflow inhibit flag to avoid aborts which cannot be caught
    // and still continue running.
    cl_inhibit_floating_point_underflow = cl_true;

    PyObject *m = Py_InitModule3("clnum", clnum_methods, clnum_doc);
    if (m == NULL)
        return;

    if (PyType_Ready(&mpf_type) < 0)
        return;

    if (PyType_Ready(&mpq_type) < 0)
        return;

    if (PyType_Ready(&cmpf_type) < 0)
        return;

    if (PyType_Ready(&cmpq_type) < 0)
        return;

    Py_INCREF(&mpf_type);
    PyModule_AddObject(m, "mpf", (PyObject *)&mpf_type);

    Py_INCREF(&mpq_type);
    PyModule_AddObject(m, "mpq", (PyObject *)&mpq_type);

    Py_INCREF(&cmpf_type);
    PyModule_AddObject(m, "cmpf", (PyObject *)&cmpf_type);

    Py_INCREF(&cmpq_type);
    PyModule_AddObject(m, "cmpq", (PyObject *)&cmpq_type);

    // Import the string support module and extract the support functions.
    PyObject *sm = PyImport_ImportModule("_clnum_str");
    if (sm == NULL)
        return;

    _mpf_clean_str = PyObject_GetAttrString(sm, "_mpf_clean_str");
    if (_mpf_clean_str == NULL)
        return;

    _mpq_clean_str = PyObject_GetAttrString(sm, "_mpq_clean_str");
    if (_mpq_clean_str == NULL)
        return;

    _cmpf_clean_str = PyObject_GetAttrString(sm, "_cmpf_clean_str");
    if (_cmpf_clean_str == NULL)
        return;

    _cmpq_clean_str = PyObject_GetAttrString(sm, "_cmpq_clean_str");
    if (_cmpf_clean_str == NULL)
        return;

    // Add the string to number converter to the clnum module so that the user
    // gets it without importing the underlying module.
    PyObject *ob = PyObject_GetAttrString(sm, "number_str");
    PyModule_AddObject(m, "number_str", ob);

    // Done with the support module so delete the reference.
    Py_DECREF(sm);
}

