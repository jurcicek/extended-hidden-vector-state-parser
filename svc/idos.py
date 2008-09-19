# -*- coding: utf-8 -*-
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

from svc.egg import PythonEgg
import httplib
import urllib
import re
import datetime
import time as time_m

def bigramIter(parent):
    i = iter(parent)
    old = i.next()
    for new in i:
        yield old, new
        old = new

class ConnectionPart(PythonEgg):
    def __init__(self, fromStation, fromTime, toStation, toTime, date=None, type=None, typeDetail=None):
        super(ConnectionPart, self).__init__()
        self.fromStation = fromStation
        self.fromTime = fromTime
        self.toStation = toStation
        self.toTime = toTime
        self.date = date
        self.type = type
        self.typeDetail = typeDetail
    
    def getAttrs(self):
        return ['fromStation', 'fromTime', 'toStation', 'toTime', 'date', 'type', 'typeDetail']

    def __repr__(self):
        s = []
        for a in self.attrs:
            v = getattr(self, a)
            if v is not None:
                s.append('%s=%r' % (a, v))
        s = ', '.join(s) 
        return 'ConnectionPart(%s)' % s

    def __eq__(self, other):
        try:
            for a in self.attrs:
                v1 = getattr(self, a)
                v2 = getattr(other, a)
                if v1 != v2:
                    return False
            return True
        except AttributeError:
            return False

    def __hash__(self):
        sum = 0
        for a in self.attrs:
            sum += hash(getattr(self, a))
        return sum % 0xffffffff


class Connection(list):
    def __init__(self, construct, notes):
        super(Connection, self).__init__(construct)
        self.notes = notes
        self.idx = 0

    def __repr__(self):
        s = super(Connection, self).__repr__()
        return 'Connection(%s, notes=%r)' % (s, self.notes)

    def __eq__(self, other):
        try:
            return super(Connection, self).__eq__(other) and self.notes == other.notes
        except AttributeError:
            return False

    def __hash__(self):
        return (super(Connection, self).__hash__() + hash(self.notes)) % 0xffffffff

    def __lt__(self, other):
        if len(self) > 0:
            t1 = self[0].fromTime
            t2 = other[0].fromTime
            return t1 < t2
        else:
            return False

    def __gt__(self, other):
        if len(self) > 0:
            t1 = self[0].fromTime
            t2 = other[0].fromTime
            return t1 > t2
        else:
            return False

class ConnectionList(PythonEgg):
    HOST = 'jizdnirady.idnes.cz'

    def __init__(self, fromStation, toStation, time, date=None, departureTime=True, onlyTrains=True):
        super(ConnectionList, self).__init__()
        self.fromStation = fromStation
        self.toStation = toStation
        self.time = time
        self.date = date
        self.departureTime = departureTime
        self.onlyTrains = onlyTrains
        self._idx = 0
        self._lst = []

    def updateLst(self, direction):
        if not self._lst:
            conn = self.idosFind(self.time, self.departureTime)
            self._lst.extend(conn)
            if direction == 'prev':
                self._idx = len(self._lst)-1
            elif direction == 'next':
                self._idx = 0
            else:
                raise ValueError('Unknown direction: %r' % direction)
        elif direction == 'prev':
            time = self._lst[0][-1].toTime
            conn = self.idosFind(time, False)
            for i in reversed(conn):
                if i not in self._lst:
                    self._lst.insert(0, i)
                    self._idx += 1
        elif direction == 'next':
            time = self._lst[-1][0].fromTime
            conn = self.idosFind(time, True)
            for i in conn:
                if i not in self._lst:
                    self._lst.append(i)
        else:
            raise ValueError('Unknown direction: %r' % direction)

    def getCurrent(self):
        return self._lst[self._idx]

    def prev(self):
        if not self._lst:
            self.updateLst('prev')
            return self.current
        elif self._idx <= 0:
            l = len(self._lst)
            self.updateLst('prev')
            if len(self._lst) == l:
                return None
        self._idx -= 1
        return self.current

    def next(self):
        if not self._lst:
            self.updateLst('next')
            return self.current
        elif self._idx >= len(self._lst)-1:
            l = len(self._lst)
            self.updateLst('next')
            if len(self._lst) == l:
                return None
        self._idx += 1
        return self.current

    def removeTags(self, s):  # odstrani z retezce tagy
        pom = s
        r = 1
        while r:
            r = re.search('(.*)<(.+?)>(.*)', pom)
            if r:
                pom = r.group(1)+r.group(3)
        return pom
        
    def convertTime(self, time):
        t = time.split(':')
        return datetime.time(int(t[0]), int(t[1]))

    def convertDate(self, date):
        current_time = time_m.localtime()
        year = current_time[0]
        d = date.split('.')
        return datetime.date(year, int(d[1]), int(d[0]))

    def parseResponse(self, response_data):
        ret = []
        phase = 0
        
        for line in response_data.splitlines():
            # najdu si prvni nalezeny spoj, kupodivu staci hledat '<tr valign="top">'
            if phase == 0 and re.search('<tr valign=\"top\">', line):
                #print "faze 0"
                phase = 1
                continue
            # najdu datum spoje    
            elif phase == 1: 
                #print "faze 1"
                match = re.search('<td align="right">(.{,6}?)<', line)
                if match:
                    spoj_datum = match.group(1)
                    phase = 2
                    continue
            # najdu zastavku
            elif phase == 2: 
                #print "faze 2"
                match = re.search('<td nowrap>(.+?)</td>', line)
                if match:
                    pom_str = match.group(1).replace('&nbsp;',' ')
                    stations = re.split('<br>', pom_str)
                    stations = map(self.removeTags, stations)
                    phase = 3
                    continue
            # najdu casy vystupu (pri prestupu ci posledniho)
            elif phase == 3: 
                #print "faze 3"
                match = re.search('<td align="right" nowrap>(.+)</td>', line)
                if match:
                    pom_str = match.group(1).replace('&#160;','')
                    toTimes = re.split('<br>', pom_str)
                    phase = 4
                    continue
            # najdu casy nastupu (prvniho ci pri prestupu)
            elif phase == 4: 
                #print "faze 4"
                match = re.search('<td align="right">(.+?)</td>', line)
                if match:
                    pom_str = match.group(1).replace('&#160;','')
                    fromTimes = re.split('<br>', pom_str)
                    phase = 5
                    continue
            # najdu pripadne poznamky 
            elif phase == 5: 
                #print "faze 5"
                match = re.search('<td align="right" nowrap>(.+?)</td>', line)
                if match:
                    pom_str = match.group(1).replace('&#160;','')
                    typeNotes = re.split('<br>', pom_str)
                    typeNotes = map(self.removeTags, typeNotes)
                    phase = 6
                    continue
            # najdu typ spoje  (bus, vlak, pesky)
            elif phase == 6: 
                #print "faze 6"
                match = re.search('<td nowrap>(.+?)</td>', line)
                if match:
                    pom_list = re.split('<br>', line)
                    types = []
                    typeDetails = []
                    for item in pom_list:
                        match3 = re.search('<a href=.+?>(.+?)<', item)
                        if match3:
                            number = match3.group(1)
                        else:
                            number = ''    
                        if re.search('bus_p.gif', item):
                            types.append("autobus")
                            typeDetails.append(number)
                        elif re.search('train_p.gif', item):
                            types.append("vlak")
                            typeDetails.append(number)
                        elif re.search('trol_p.gif', item):
                            types.append("trolejbus")
                            typeDetails.append(number)
                        elif re.search('tram_p.gif', item):
                            types.append("tramvaj")
                            typeDetails.append(number)
                        elif re.search('metro_p.gif', item):
                            types.append("metro")
                            typeDetails.append(number)
                        elif re.search('foot_p.gif', item):
                            match2 = re.search('esun asi (\d+) min', item)
                            types.append(u"přesun pěšky")
                            if match2:
                                typeDetails.append(match2.group(1)+' minuty')
                            else:    
                                typeDetails.append('')
                        else:
                            types.append('')
                            typeDetails.append('')
                    phase = 7
                    continue
            # najdu zaverecnou poznamku - delka cesty apod.
            elif phase == 7: 
                #print "faze 7"
                match = re.search('<td colspan="11">(.+?)</td>', line)
                if match:
                    note = match.group(1)
                    
                    stations2 = list(bigramIter(stations))
                    l = len(stations2)
                    del fromTimes[l:]
                    del toTimes[:-l]
                    del types[l:]
                    del typeDetails[l:]
                    del typeNotes[l:]
                    ret.append(Connection([], note))
                    for (fromStation, toStation), fromTime, toTime, type, typeDetail in zip(stations2, fromTimes, toTimes, types, typeDetails):
                        fromTime = self.convertTime(fromTime)
                        toTime = self.convertTime(toTime)
                        date = self.convertDate(spoj_datum)
                        c = ConnectionPart(fromStation, fromTime, toStation, toTime, date, type, typeDetail)
                        ret[-1].append(c)

                    phase = 0
                    continue
        return ret

    def idosFind(self, time, departureTime):
        time_s = time.strftime('%H:%M')
        if self.date is not None:
            date_s = self.date.strftime('%d.%m.%Y')
        else:
            current_time = time_m.localtime()
            date_s = datetime.date(*current_time[:3]).strftime('%d.%m.%Y')

        if self.onlyTrains:
            TT = 'a'
        else:
            TT = 'X'

        if departureTime:
            connIsDep = 1
        else:
            connIsDep = 0

        station_from = self.fromStation.encode('cp1250')
        station_to = self.toStation.encode('cp1250')

        station_from = urllib.quote(station_from)
        station_to = urllib.quote(station_to)
        time = urllib.quote(time_s)
        date = urllib.quote(date_s)

        headers1 = { "Host": self.HOST,
                    "User-Agent": "User-Agent: Mozilla/5.0 (Windows; U; Windows NT 5.1; cs-CZ; rv:1.7.8) Gecko/20050511 Firefox/1.0.4",
                    "Accept": "text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
                    "Accept-Language": "cs,en-us;q=0.7,en;q=0.3",
                    "Accept-Encoding": "text/plain",
                    "Accept-Charset": "ISO-8859-2,utf-8;q=0.7,*;q=0.7",
                    "Referer": "http://%s/ConnForm.asp" % self.HOST,
                    "Keep-Alive": "300",
                    "Connection": "keep-alive",
                  }

        conn = httplib.HTTPConnection(self.HOST)
        conn.request("GET", "/connform.asp?tt=%s&cl=C HTTP/1.1" % (TT,), '', headers1)

        response = conn.getresponse()
        response_data = response.read()

        match = re.search('name="link" value="(\w{,6})"', response_data)
        if match:
            param_link = match.group(1)
        else:
            conn.close()
            raise ValueError("Cannot get link attribute")

        headers2 = headers1.copy()
        headers2["Content-type"] = "application/x-www-form-urlencoded"

        data = 'FromStn=%s&FromList=-1&ToStn=%s&ToList=-1&ViaStn=&ViaList=-1&ConnDate=%s&ConnTime=%s&ConnIsDep=%d&ConnAlg=%s&Prest=%s&search=Vyhledat&tt=%s&changeext=0&Mask1=-1&Min1=5&Max1=240&Std1=1&Mask2=-1&Min2=0&Max2=240&Std2=0&beds=0&alg=1&chn=5&odch=50&odcht=0&ConnFromList=-1&ConnToList=-1&ConnViaList=-1&recalc=0&pars=0&process=0&link=%s' % (station_from, station_to, date, time, connIsDep, 1, 3, TT, param_link) # prestup povolen, max_prestupu

        conn.request("POST", "/ConnForm.asp?tt=%s HTTP/1.0" % (TT,), data, headers2)
        response = conn.getresponse()
        response_data = response.read()

        if response.status == 200:
            return []
        elif response.status == 302:
            redirect = response.getheader("location", "")
            if not re.search('ConnRes', redirect):
                raise ValueError("Error")

            conn.request("GET", "/"+redirect+" HTTP/1.0", '', headers1)

            response = conn.getresponse()
            response_data = response.read()

            if re.search('ErrRes', response.getheader('location', "")):
                raise ValueError("Error")

            return self.parseResponse(response_data.decode('cp1250')) 


if __name__ == '__main__':
    lst = ConnectionList(u'Plzeň', u'Písek [PI]', datetime.time(16, 29), datetime.date(2007, 11, 7), departureTime=False)
    for i in range(20):
        print lst.next()
    for i in range(30):
        print lst.prev()
    for i in range(50):
        print lst.next()
