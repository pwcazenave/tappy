#!/usr/bin/env python

"""
NAME:
    pad.py  

SYNOPSIS:
    import pad
    a = scipy.arange(100)

    # Use the maximum value of the input vector to pad.
    b = pad.maximum(a, (pad_length_before, after_stat_len))

    # Use the minimum value of the input vector to pad.
    b = pad.minimum(a, (pad_length_before, after_stat_len))

    # Use the median value of the input vector to pad.
    b = pad.median(a, (pad_length_before, after_stat_len))

    # Use the mean value of the input vector to pad.
    b = pad.mean(a, (pad_length_before, after_stat_len))

    # Use the supplied values to pad with before and after.
    b = pad.constant(a, (pad_length_before, after_stat_len),
                        (constant_before, constant_after))

    # Ramp for the edge values to the supplied values.
    b = pad.linear_ramp(a, (pad_length_before, after_len_to_ramp),
                    (end_before, end_after))

    # Reflect the edge values of the array to pad.
    b = pad.reflect(a, (pad_length_before, after_len_to_reflect),

    # Wrap from the other edge of the array
    b = pad.wrap(a, (before_len_to_wrap, after_len_to_wrap))

DESCRIPTION:
    Set of functions to pad a rank 1 array.

OPTIONS:
    -h,--help        this message
    -v,--version     version
    -d,--debug       turn on debug messages
    --bb=xyz         set option bb to xyz

EXAMPLES:
    1. As library
        import pad
        ...

#Copyright (C) 2005  Tim Cera
#
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


"""
#===imports======================
import scipy as N

#===globals======================
modname = "pad"
__version__ = "0.1"

#---other---
__all__ = ['minimum', 
           'maximum', 
           'mean', 
           'median',
           'linear_ramp',
           'reflect',
           'constant',
           'wrap',
           ]

_help_string_matrix = "matrix: N-dimensional matrix"
_help_string_pad_width = """pad_width: how many values padded to each end of the vector for each axis
           ((before, after),) * N.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes"""
_help_string_stat_len = """stat_len: how many values at each end of vector to calculate the statistic
          ((before_len, after_len),) * N.rank(matrix)
          (len,) is a shortcut for before = after = len for all dimensions"""
_help_string_statistic = """statistic: ["mean", "median", "maximum", "minimum"], default is "mean" """
_help_string_returns_matrix = "RETURNS -> N-dimensional matrix"

#====================================
# Exception classes
class PadWidthWrongNumberOfValues(Exception):
    ''' 
    Exception class to catch where number of pad width values doesn't match
    rank + 1.
    '''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
#====================================


########
# Private utility functions.
def __create_vector(vector, pad_tuple, before_val, after_val):
    ''' 
    Private function which creates the padded vector to mean, maximum,
    minimum, and median.
    '''
    vector[:pad_tuple[0]] = before_val
    vector[-pad_tuple[1]:] = after_val
    return vector


def __validate_tuple(vector, pad_width):
    '''
    Private function which does some checks and reformats the pad_width
    tuple.
    '''
    shapelen = len(N.shape(vector))
    if (        isinstance(pad_width, (tuple, list)) 
            and isinstance(pad_width[0], (tuple,list))
            and len(pad_width) == shapelen):
        return pad_width
    if (        isinstance(pad_width, (tuple, list)) 
            and isinstance(pad_width[0], (int,float,long))
            and len(pad_width) == 1):
        return ((pad_width[0], pad_width[0]),) * shapelen
    if (        isinstance(pad_width, (tuple, list)) 
            and isinstance(pad_width[0], (int,float,long))
            and len(pad_width) == 2):
        return (pad_width,) * shapelen
    raise PadWidthWrongNumberOfValues(pad_width)

def __reverse(in_vector):
    '''
    Private function to reverse a vector.
    '''
    in_list = in_vector.tolist()
    in_list.reverse()
    return N.array(in_list).astype(in_vector.dtype)

def __loop_across(matrix, pad_width, function, **kw):
    '''
    Private function to prepare the data for the N.apply_along_axis command
    to move through the matrix.
    '''
    if kw.has_key('stat_len') and kw['stat_len']:
        kw['stat_len'] = __validate_tuple(matrix, kw['stat_len'])
    else:
        kw['stat_len'] = None
    pad_width = __validate_tuple(matrix, pad_width)
    rank = range(len(matrix.shape))
    total_dim_increase = [N.sum(pad_width[i]) for i in rank]
    offset_slices = [slice(pad_width[i][0],  pad_width[i][0] + matrix.shape[i]) for i in rank]
    new_shape = N.array(matrix.shape) + total_dim_increase
    newmat = N.zeros(new_shape).astype(matrix.dtype)
    newmat[offset_slices] = matrix
    if len(matrix.shape) > 1:
        for iaxis in rank:
            N.apply_along_axis(function, 
                               iaxis, 
                               newmat, 
                               pad_width[iaxis], 
                               iaxis, 
                               kw)
        return newmat
    else:
        return function(newmat, pad_width[0], 0, kw)

def __create_pad_vectors(vector, pad_tuple, iaxis, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    if kw['stat_len']:
        stat_len = kw['stat_len'][iaxis]
        bvec = vector[pad_tuple[0]:pad_tuple[0] + stat_len[0]]
        avec = vector[-pad_tuple[1] - stat_len[1]:-pad_tuple[1]]
    else:
        bvec = avec = vector[pad_tuple[0]:-pad_tuple[1]]
    return (bvec, avec)

def __maximum(vector, pad_tuple, iaxis, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    bvec, avec = __create_pad_vectors(vector, pad_tuple, iaxis, kw)
    return __create_vector(vector, pad_tuple, N.argmax(bvec), N.argmax(avec))

def __minimum(vector, pad_tuple, iaxis, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    bvec, avec = __create_pad_vectors(vector, pad_tuple, iaxis, kw)
    return __create_vector(vector, pad_tuple, N.argmin(bvec), N.argmin(avec))

def __median(vector, pad_tuple, iaxis, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    bvec, avec = __create_pad_vectors(vector, pad_tuple, iaxis, kw)
    return __create_vector(vector, pad_tuple, N.median(bvec), N.median(avec))

def __mean(vector, pad_tuple, iaxis, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    bvec, avec = __create_pad_vectors(vector, pad_tuple, iaxis, kw)
    return __create_vector(vector, pad_tuple, N.average(bvec), N.average(avec))

def __constant(vector, pad_tuple, iaxis, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    constant_v = kw['constant'][iaxis]
    return __create_vector(vector, pad_tuple, constant_v[0], constant_v[1])

def __linear_ramp(vector, pad_tuple, iaxis, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    end_value = kw['end_value'][iaxis]
    before_delta = (vector[pad_tuple[0]] - end_value[0])/float(pad_tuple[0])
    after_delta = (vector[-pad_tuple[1] - 1] - end_value[1])/float(pad_tuple[1])

    before_vector = N.ones((pad_tuple[0],)) * end_value[0]
    before_vector = before_vector.astype(vector.dtype)
    for i in range(len(before_vector)):
        before_vector[i] = before_vector[i] + i*before_delta

    after_vector = N.ones((pad_tuple[1],)) * end_value[1]
    after_vector = after_vector.astype(vector.dtype)
    for i in range(len(after_vector)):
        after_vector[i] = after_vector[i] + i*after_delta
    after_vector = __reverse(after_vector)

    return __create_vector(vector, pad_tuple, before_vector, after_vector)

def __reflect(vector, pad_tuple, iaxis, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    before_vector = __reverse(vector[pad_tuple[0] + 1:2*pad_tuple[0] + 1])
    after_vector = __reverse(vector[-2*pad_tuple[1] - 1:-pad_tuple[1] - 1])
    return __create_vector(vector, pad_tuple, before_vector, after_vector)

def __wrap(vector, pad_tuple, iaxis, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    before_vector = vector[-(pad_tuple[1] + pad_tuple[0]):-pad_tuple[1]]
    after_vector = vector[pad_tuple[0]:pad_tuple[0] + pad_tuple[1]]
    return __create_vector(vector, pad_tuple, before_vector, after_vector)

#
########

def maximum(matrix, pad_width=(1, ), stat_len=None):
    """ 
Pads with the maximum value of all or part of the vector along each axis.

matrix: N-dimensional matrix
pad_width: how many values padded to each end of the vector for each axis
           ((before, after),) * N.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
stat_len: how many values at each end of vector to calculate the statistic
          ((before_len, after_len),) * N.rank(matrix)
          (len,) is a shortcut for before = after = len for all dimensions
statistic: ["mean", "median", "maximum", "minimum"], default is "mean"
RETURNS -> N-dimensional matrix
    """
    return __loop_across(matrix, pad_width, __maximum, stat_len=stat_len)

def minimum(matrix, pad_width=(1, ), stat_len=None):
    """ 
Pads with the minimum value of all or part of the vector along each axis.

matrix: N-dimensional matrix
pad_width: how many values padded to each end of the vector for each axis
           ((before, after),) * N.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
stat_len: how many values at each end of vector to calculate the statistic
          ((before_len, after_len),) * N.rank(matrix)
          (len,) is a shortcut for before = after = len for all dimensions
statistic: ["mean", "median", "maximum", "minimum"], default is "mean"
RETURNS -> N-dimensional matrix

    """
    return __loop_across(matrix, pad_width, __minimum, stat_len=stat_len)

def median(matrix, pad_width=(1, ), stat_len=None):
    """ 
Pads with the median value of all or part of the vector along each axis.

matrix: N-dimensional matrix
pad_width: how many values padded to each end of the vector for each axis
           ((before, after),) * N.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
stat_len: how many values at each end of vector to calculate the statistic
          ((before_len, after_len),) * N.rank(matrix)
          (len,) is a shortcut for before = after = len for all dimensions
statistic: ["mean", "median", "maximum", "minimum"], default is "mean"
RETURNS -> N-dimensional matrix

    """
    return __loop_across(matrix, pad_width, __median, stat_len=stat_len)

def mean(matrix, pad_width=(1, ), stat_len=None):
    """ 
Pads with the mean value of all or part of the vector along each axis.

matrix: N-dimensional matrix
pad_width: how many values padded to each end of the vector for each axis
           ((before, after),) * N.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
stat_len: how many values at each end of vector to calculate the statistic
          ((before_len, after_len),) * N.rank(matrix)
          (len,) is a shortcut for before = after = len for all dimensions
statistic: ["mean", "median", "maximum", "minimum"], default is "mean"
RETURNS -> N-dimensional matrix

    """
    return __loop_across(matrix, pad_width, __mean, stat_len=stat_len)

def constant(matrix, pad_width=(1, ), constant_v=(0, )):
    """ 
Pads with a constant value.

matrix: N-dimensional matrix
pad_width: how many values padded to each end of the vector for each axis
           ((before, after),) * N.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
constant: the value to set the padded values to
          ((before_constant, after_constant),) * N.rank(matrix)
          (constant,) is a shortcut for before = after = constant for all dimensions
RETURNS -> N-dimensional matrix

    """
    constant_v = __validate_tuple(matrix, constant_v)
    return __loop_across(matrix, pad_width, __constant, constant=constant_v)

def linear_ramp(matrix, pad_width=(1, ), end_value=(0, )):
    """ 
Pads with the linear ramp between end_value and the begining/end of the vector along each axis.

matrix: N-dimensional matrix
pad_width: how many values padded to each end of the vector for each axis
           ((before, after),) * N.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
end_value: value to ramp to
          ((before_len, after_len),) * N.rank(matrix)
          (len,) is a shortcut for before = after = len for all dimensions
RETURNS -> N-dimensional matrix

    """
    end_value = __validate_tuple(matrix, end_value)
    return __loop_across(matrix, pad_width, __linear_ramp, end_value=end_value)

def reflect(matrix, pad_width=(1, )):
    """ 
Pads with the reflection of the vector mirrored on the first and last values of the vector along each axis.

matrix: N-dimensional matrix
pad_width: how many values padded to each end of the vector for each axis
           ((before, after),) * N.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
RETURNS -> N-dimensional matrix
    """
    # TODO self.pad_length_before & self.pad_length_after < len(self.vector)
    return __loop_across(matrix, pad_width, __reflect)

def wrap(matrix, pad_width=(1, )):
    """ 
Pads with the wrap of the vector along the axis.  The first values are used to pad the end and the end values are used to pad the beginning.

matrix: N-dimensional matrix
pad_width: how many values padded to each end of the vector for each axis
           ((before, after),) * N.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
RETURNS -> N-dimensional matrix
    """
    return __loop_across(matrix, pad_width, __wrap)

