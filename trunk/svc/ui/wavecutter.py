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

import struct

class WAVECutter(object):
    head_fmt = '4sI4s4sI'
    fmt_fmt = 'HHIIHH'
    data_fmt = '4sI'
    head_len = struct.calcsize(head_fmt)
    fmt_len = struct.calcsize(fmt_fmt)
    data_len = struct.calcsize(data_fmt)

    def __init__(self, fn):
        f = file(fn, 'rb')
        self.fn = fn
        try:
            head = f.read(self.head_len)
            RIFF, length, WAVE, FMT, flength = struct.unpack(self.head_fmt, head)
            fmt = f.read(flength)
            self.format, self.chans, self.sampsRate, self.bpsec, self.bpsample, self.bpchan = struct.unpack(self.fmt_fmt, fmt)
            data = f.read(self.data_len)
            DATA, self.dlength = struct.unpack(self.data_fmt, data)
            self.thlength = 20 + flength + 8
            if RIFF != 'RIFF' \
            or WAVE != 'WAVE' \
            or FMT != 'fmt ' \
            or DATA != 'data':
                raise IOError("Not WAVE file: %s" % fn)
        finally:
            f.close()
    
    def writeSlice(self, fn, f, t, error=None, pad_sec=0.):
        pad_bytes = long(self.sampsRate * pad_sec) * self.bpsample
        padding = '\xff' * pad_bytes

        start_byte = long(self.sampsRate * f) * self.bpsample
        end_byte = long(self.sampsRate * t) * self.bpsample
        dlength = end_byte - start_byte

        f = file(self.fn, 'rb')
        try:
            f.seek(self.thlength + start_byte)
            pcm_data = padding + f.read(dlength) + padding

            if len(pcm_data) == 0:
                raise IOError("Error reading WAVE - no data")
            if len(pcm_data) != dlength + 2*pad_bytes:
                msg = "Missing %d bytes while reading WAVE data" % (dlength - len(pcm_data))
                if error is None:
                    raise IOError(msg)
                else:
                    print >> error, 'Warning: %s' % msg
        finally:
            f.close()


        fmt_chunk = struct.pack(self.fmt_fmt, self.format, self.chans, self.sampsRate, self.bpsec, self.bpsample, self.bpchan)
        data_chunk = struct.pack(self.data_fmt, 'data', len(pcm_data)) + pcm_data
        length = len(fmt_chunk) + len(data_chunk)
        head_chunk = struct.pack(self.head_fmt, 'RIFF', length, 'WAVE', 'fmt ', 16)

        f = file(fn, 'wb')
        try:
            f.write(head_chunk)
            f.write(fmt_chunk)
            f.write(data_chunk)
        finally:
            f.close()
