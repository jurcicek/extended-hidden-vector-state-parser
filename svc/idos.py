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
import os
import sys
import httplib
import urllib
import re
import string
import getopt
import time
import codecs
from pprint import pprint



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

ZPRACOVAT_ARGUMENTY = 1


class IDOS:
    """ Trida IDOS zprostradkova vyhledavani dopravnich spojeni prostrednictvim serveru Idos """

    # konstanty pro navratove kody
    KOD_SPOJ_NALEZEN = 0
    KOD_NEZNAMY_PARAMETR_LINK = 1
    KOD_NEJEDNOZNACNE_KONCOVE_BODY = 2
    KOD_SPOJ_NENALEZEN = 3
    KOD_OBJEKT_NENALEZEN = 4
    KOD_DETAIL_ZISKAN = 5
    KOD_DETAIL_NELZE_ZISKAT = 6


    def __init__(self):

        # vyhledavaci kody pro identifikaci typu spojeni pri hledani pres idos
        self.DICT_VYHLEDAVACI_KODY1 = {
            "BRNO": "tt=f",
            "VLAK": "tt=a",#tt=a&p=CD",
            "BUS": "tt=b",
            "KOMB": "tt=X&cl=C",
            "PRAHA": "tt=e",
            "OSTRAVA": "tt=g",
            "LIBEREC": "tt=LI",
        }
    
        self.DICT_VYHLEDAVACI_KODY2 = {
            "BRNO": "tt=f",
            "VLAK": "tt=a",#tt=a&p=CD",
            "BUS": "tt=b",
            "KOMB": "tt=c",
            "PRAHA": "tt=e",
            "OSTRAVA": "tt=g",
            "LIBEREC": "tt=LI",
        }
    
        self.TYPY_SPOJU = self.DICT_VYHLEDAVACI_KODY1.keys()  #["VLAK", "BUS", "KOMB", "BRNO", "PRAHA"]
    
        self.TYP_SPOJE="VLAK"    # urcuje jaky typ spoje se bude hledat
        self.ODKUD = u"Brno"  # pocatek cesty
        self.ODKUD2=""           # upresneny pocatek cesty pomoci kodu
        self.KAM = u"Plzen"     # cil cesty
        self.KAM2=""             # upresneny cil cesty pomoci kodu
        #self.KAM2="9%254%25682%21"
        self.KDY = u"29.12.2008"   
        self.CAS = u"11:00"
        self.CAS_URCUJE_ODJEZD = 1  # 1 = cas urcuje odjezd, 0 = cas urcuje prijezd
        self.MAX_PRESTUPU = 3    # maximalni pocet prestupu (neni vzdy idosem respektovan)
        self.MAX_SPOJU = 5       # maximalni pocet nalezenych spoju
    
        self.VYBER_ODKUD = []       # obsahuje seznam moznosti pri nepresne specifikovanem vyberu
        self.VYBER_KAM = []         # obsahuje seznam moznosti pri nepresne specifikovanem vyberu
        self.NALEZENA_SPOJENI = []  # obsahuje nalezena spojeni
                               # kazde spojeni na nasledujici strukturu
                               # [datum, [prvni_spoj], ...., [posledni_spoj], poznamky]
                               # pricemz kazdy ze spoju ma nasledujici strukturu
                               # [prijezd, odjezd, zastavka, poznamka, typ spoje, cislo spoje]

        self.DICT_URL_DETAILY_SPOJU = {}  # slovnik s URL adresami detailu nalezenych spojeni
                                          # jednotlive polozky jsou slovniky s klici 
                                          # trasa (pro trasu spoje), poloha (pro zpozdeni vlaku), razeni (pro razeni vlaku)
        self.DICT_DETAILY_SPOJU = {}  # slovnik s detaily nalezenych spojeni
                                      # kazda polozka ma tvar:
                                      # [zastavka, prijezd, odjezd, poznamka, kilometry]
        self.DICT_ZPOZDENI_VLAKU = {}  # slovnik s informaceni o zpozdeni vlaku


        self.DATA = ""              # do teto promenne se ulozi data ziskana z idosu (html stranka)
        self.DATA2 = ""             # do teto promenne se ulozi data ziskana z idosu - detail spojeni (html stranka), ale pouze jen pro posledni dotazovane spojeni
    
        self.NAVRATOVY_KOD = None   # pro ulozeni navratoveho kodu identifikujiciho vysledek vyhledavani
        self.POPIS_CHYBY = ""       # textovy popis chyby
    
        self.CLI_MOD = 0   # ovlivnuje chovani programu (0 = zadne vystupy, 1 = vypis pro batch mode, 2 = interaktivni pri spusteni z konole
        self.VYPSAT_TRASU_SPOJE = 0  # povoluje/zakazuje  vypis zastavek na trase jednotlivych spoju, 0 = nic, 1 = zastavky na trase, 2 = vsechny zastavky 
        self.VYPSAT_ZPOZDENI_VLAKU = 0  # povoluje/zakazuje dohledavani a vypis informace o zpozdeni vlaku


        self.KODOVANI_IDOS = 'cp1250'   # kodovani pouzivane idosem
        self.KODOVANI_SYSTEM = 'utf_8'  # kodovani v systemu - ma vyznam pro tiskove vystupy, pri pouziti tridy samotne neni dulezita

        self.HEADERS = { 
                "Host": "jizdnirady.idnes.cz",
                "User-Agent": "User-Agent: Mozilla/5.0 (Windows; U; Windows NT 5.1; cs-CZ; rv:1.7.8) Gecko/20050511 Firefox/1.0.4",
                "Accept": "text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
                "Accept-Language": "cs,en-us;q=0.7,en;q=0.3",
                "Accept-Encoding": "text/plain",
                "Accept-Charset": "ISO-8859-2,utf-8;q=0.7,*;q=0.7",
                "Referer": "http://jizdnirady.idnes.cz/ConnForm.asp",
                "Keep-Alive": "300",
                "Connection": "keep-alive",
              }
    
        self.IDOS_URL = "www.vlak.cz"


    
    
    def generator_dat(self, data = 1):
        """ generator posila obsah retezce self.DATA nabo self.DATA2 po jednotlivych radcich """

        if data == 1:
            radky = self.DATA.splitlines()
        else:
            radky = self.DATA2.splitlines()

        for i in range(len(radky)):
            yield radky[i]
        


    def odstran_tagy(self, s):  
        """ odstrani z retezce tagy """

        pom = s
        r = 1
        while r:
            r = re.search('(.*)<(.+?)>(.*)', pom)
            if r:
                pom = r.group(1)+r.group(3)
        return pom



    def nahrad_nechtene_retezce(self, s):  
        """ odstrani ci upravi nektere nechtene retezce """

        s = s.replace(u'&nbsp;',u' ')
        s = s.replace(u',,',u',')
        s = s.replace(u'&#160;',u'')
        return s



    def vyhledej_dopravni_spojeni(self):
        """ Vyhleda dopravni spojeni, v pripade CLI je i vytiskne """

        self.posli_dotaz_na_idos()
        self.zpracuj_ziskana_data()

        if self.VYPSAT_TRASU_SPOJE:
            self.vyhledej_detaily_spoju()
        if self.VYPSAT_ZPOZDENI_VLAKU:
            self.vyhledej_zpozdeni_vlaku()

        if self.CLI_MOD > 0:
            self.vypis_zpracovana_data()



    def vyhledej_detaily_spoju(self):
        """ Vyhleda detaily k nalezenych dopravnim spojenim """
        
        self.DICT_DETAILY_SPOJU = {}
        
        # projdu nalezena spojeni a pro kazdy uvedeny spoj dohledam detaily
        for spojeni in self.NALEZENA_SPOJENI:

            # preskocim datum a poznamky
            for spoj in spojeni[1:-1]:

                # pokud pro uvedene spojeni, neni-li jeste ve slovniku, dohledam detaily
                if (len(spoj) == 6):
                    cislo = spoj[5]

                    if not cislo in self.DICT_DETAILY_SPOJU:
                                 
                        # ziskam z idosu detail o spoji
                        kod = self.ziskej_z_idosu_detail_spoje(cislo, "trasa")
                        # detail o dopravnim spoji nalezen
                        if kod == self.KOD_DETAIL_ZISKAN:
                            self.DICT_DETAILY_SPOJU[cislo] = self.parsuj_detail_spoje()
                        else:
                            pass



    def vyhledej_zpozdeni_vlaku(self):
        """ Vyhleda informace o zpozdeni vlaku """
        
        self.DICT_ZPOZDENI_VLAKU = {}
        
        # projdu nalezena spojeni a pro kazdy uvedeny spoj dohledam detaily
        for spojeni in self.NALEZENA_SPOJENI:

            # preskocim datum a poznamky
            for spoj in spojeni[1:-1]:

                # pokud pro uvedene spojeni, neni-li jeste ve slovniku a mam-li ulozene URL pro zpozdeni, pak dohledam detaily
                if (len(spoj) == 6):
                    cislo = spoj[5]
                    if cislo and (not cislo in self.DICT_ZPOZDENI_VLAKU) and ("poloha" in self.DICT_URL_DETAILY_SPOJU[cislo]):
                        # ziskam z idosu detail o spoji
                        kod = self.ziskej_z_idosu_detail_spoje(cislo, "poloha")
                        # detail o dopravnim spoji nalezen
                        if kod == self.KOD_DETAIL_ZISKAN:
                            zpozdeni = self.parsuj_zpozdeni_vlaku()
                            if zpozdeni:
                                self.DICT_ZPOZDENI_VLAKU[cislo] = self.parsuj_zpozdeni_vlaku()
                        else:
                            pass
            
            

    def zpracuj_ziskana_data(self):
        """ Zpracuje odpoved ziskanou z idosu """
        
        kod = self.NAVRATOVY_KOD
        
        if kod == self.KOD_NEJEDNOZNACNE_KONCOVE_BODY:
            # nejednoznacne zadane koncove body     
            self.parsuj_koncove_body()

        elif kod == self.KOD_SPOJ_NALEZEN:
            # hledane spojeni bylo nalezeno
            self.parsuj_nalezena_spojeni()

        else:
            # behem k hledani doslo k chybe 
            pass



    def vypis_zpracovana_data(self):
        """ V zavislosti na pouzitem rozhrani prezentuje nalezene vysledky """
    
        kod = self.NAVRATOVY_KOD

        if kod == self.KOD_NEJEDNOZNACNE_KONCOVE_BODY:
            # nejednoznacne zadane koncove body     
            
            #print self.VYBER_ODKUD
            #print self.VYBER_KAM

            if self.CLI_MOD == 2:  # interaktivni mod

                # nepresne zadane misto odkud
                if len(self.VYBER_ODKUD) > 1:
                    volba = self.CLI_vyber_z_menu(self.VYBER_ODKUD, u"Upřesněte počátek cesty")
                    self.ODKUD2 = self.VYBER_ODKUD[volba].split(u":")[-1]
    
                # nepresne zadane misto kam
                if len(self.VYBER_KAM) > 1:
                    volba = self.CLI_vyber_z_menu(self.VYBER_KAM, u"Upřesněte cíl cesty")
                    self.KAM2 = self.VYBER_KAM[volba].split(u":")[-1]
                
                #print self.ODKUD2, self.KAM2
                
                # novy dotaz s upresnenymi udaji
                self.vyhledej_dopravni_spojeni()

	    if self.CLI_MOD == 1:  # batch mod
		# vypisi nabidku moznosti pro koncove body
                print(u"CHOOSE".encode(self.KODOVANI_SYSTEM))
                print(u"FromList".encode(self.KODOVANI_SYSTEM))
                for misto in self.VYBER_ODKUD:
                    print(misto.encode(self.KODOVANI_SYSTEM))
                # cast kam
                print(u"ToList".encode(self.KODOVANI_SYSTEM))
                for misto in self.VYBER_KAM:
                    print(misto.encode(self.KODOVANI_SYSTEM))
                print(u"ENDCHOOSE".encode(self.KODOVANI_SYSTEM))

        elif kod == self.KOD_SPOJ_NALEZEN:
            # hledane spojeni bylo nalezeno
            #self.parsuj_nalezena_spojeni()

            # vypisu nalezena spojeni
            for spojeni in self.NALEZENA_SPOJENI:
                datum = u"Datum: "+spojeni[0]
                poznamka = spojeni[-1]
                print u"--------------------".encode(self.KODOVANI_SYSTEM)
                print datum.encode(self.KODOVANI_SYSTEM)
                vypsane_detaily = []   # pro ktere spoje vypisi detaily
                # projdu jednotlive spoje
                for spoj in spojeni[1:-1]:
                    spoj_vypis = spoj[0]+u'  '+spoj[1]+u'  '+spoj[2]  # prijezd, odjezd, zastavka
                    if (len(spoj)>3) and spoj[3]:  # poznamka
                        spoj_vypis += u", "+spoj[3]
                    if (len(spoj)>4) and spoj[4]:  # typ spoje
                        spoj_vypis += u", "+spoj[4]
                    if (len(spoj)>5) and spoj[5]:  # jmeno (cislo) spoje
                        spoj_vypis += u" "+spoj[5]
                        vypsane_detaily.append(spoj[5])
                        if self.VYPSAT_ZPOZDENI_VLAKU and (spoj[5] in self.DICT_ZPOZDENI_VLAKU):
                            spoj_vypis += u", zpoždění "+self.DICT_ZPOZDENI_VLAKU[spoj[5]]
                    print spoj_vypis.encode(self.KODOVANI_SYSTEM)
                if poznamka:
                    print
                    print (u'Pozn.: '+poznamka).encode(self.KODOVANI_SYSTEM)
                if self.VYPSAT_TRASU_SPOJE:  # vypisi detaily o jednotlivych spojich
                    for cislo in vypsane_detaily:
                        print
                        self.vypis_detaily_spoje(cislo)
            print

        else:
            # behem k hledani doslo k chybe 
            print self.POPIS_CHYBY.encode(self.KODOVANI_SYSTEM)


    
    def vypis_detaily_spoje(self, cislo):
        """ Vypise detaily zadaneho spoje. Tyto detaily jiz musi byt nacteny ve slovniku self.DICT_DETAILY_SPOJU """
        
        if cislo in self.DICT_DETAILY_SPOJU:
            detaily = self.DICT_DETAILY_SPOJU[cislo]
            
            # podle typu vypisu profiltruji vypisovane zastavky
            if self.VYPSAT_TRASU_SPOJE == 1:   # vypisuji pouze zastavky mezi nastupem a vystupem
                vypsat = False
                vypisovane_zastavky = []
                for i in range(1, len(detaily)):
                    if detaily[i][0][0] == u'*' and (not vypsat):  # zastavka kde nastupuji
                        vypsat = True
                        vypisovane_zastavky.append(i)
                    elif detaily[i][0][0] == u'*' and vypsat:  # zastavka kde vystupuji
                        vypisovane_zastavky.append(i)
                        break
                    elif vypsat: # jsem mezi nastupni a vystupni zastavkou
                        vypisovane_zastavky.append(i)  
                    
            elif self.VYPSAT_TRASU_SPOJE == 2:  # vypisuji vsechny zastavky
                vypisovane_zastavky = range(1, len(detaily))
            
            else:  # neznama hodnota, nemelo by nastat
                return
            
            # najdu nejvetsi sirku nazvu a poznamky
            hlavicka = u"=== "+detaily[0]+u" ==="
            max1 = len(hlavicka)
            max2 = 3
            for i in vypisovane_zastavky:
                max1 = max(max1, len(detaily[i][0]))
                max2 = max(max2, len(detaily[i][3]))
            max1 += 3
            if max2 > 0:
                max2 += 2

            s = hlavicka.ljust(max1)+u' Příj. '+u'  Odj.'+u'  Pozn.'
            print s.encode(self.KODOVANI_SYSTEM)

            for i in vypisovane_zastavky:
                zastavka = detaily[i][0]
                if zastavka[0] == u'*':
                    zastavka = zastavka.upper()
                else:
                    zastavka = u' '+zastavka
                s = zastavka.ljust(max1)+detaily[i][1].center(7)+detaily[i][2].center(7)+u'  '+detaily[i][3].ljust(max2)+detaily[i][4].rjust(4)+u' km'
                print s.encode(self.KODOVANI_SYSTEM)

    

    def posli_dotaz_na_idos(self):
        """ Posle dotaz na IDOS a ulozi ziskana data a status odpovedi """

        if self.ODKUD2 == "":
            odkud2 = urllib.quote(self.ODKUD.encode(self.KODOVANI_IDOS))
        else:
            odkud2 = self.ODKUD2.encode(self.KODOVANI_IDOS)
        if self.KAM2 == "":
            kam2 = urllib.quote(self.KAM.encode(self.KODOVANI_IDOS))
        else:
            kam2 = self.KAM2.encode(self.KODOVANI_IDOS)
        
        kdy = urllib.quote(self.KDY.encode(self.KODOVANI_IDOS))
        cas = urllib.quote(self.CAS.encode(self.KODOVANI_IDOS))
        #print odkud2, kam2, kdy, cas
    
        # PRVNI DOTAZ, cilem je zjistit hodnotu parametru link
    
        conn = httplib.HTTPConnection(self.IDOS_URL)
        conn.request("GET", "/ConnForm.asp?"+self.DICT_VYHLEDAVACI_KODY1[self.TYP_SPOJE]+" HTTP/1.1", '', self.HEADERS)
    
        #print "posilam dotaz"
        r = conn.getresponse()
        #print "Odpoved:", r.status, r.reason
        data = r.read()
        #print data
        
        parametr_link = ""
        
        vyber = re.search('name="link" value="(\w{,6})"', data)
        if vyber:
            parametr_link = vyber.group(1)
            #print "Hodnota link:", param_link
        else:
            #print "nepodarilo se zjistit hodnotu parametru 'link'"
            self.POPIS_CHYBY = u"nepodařilo se zjistit hodnotu parametru 'link'"
            conn.close()
            self.NAVRATOVY_KOD = self.KOD_NEZNAMY_PARAMETR_LINK
            return

        # DRUHY DOTAZ, posilam udaje o hledanem spoji
    
        # pridam k hlavicce content-type
        self.HEADERS["Content-type"] = "application/x-www-form-urlencoded"
    
        max_prestupu = self.MAX_PRESTUPU
        if max_prestupu:
            prestup_povolen = 1
        else:   
            prestup_povolen = 0
            max_prestupu = 1
    
        posilana_data = 'FromStn=%s&FromList=-1&ToStn=%s&ToList=-1&ViaStn=&ViaList=-1&ConnDate=%s&ConnTime=%s&ConnIsDep=%s&ConnAlg=%s&Prest=%s&search=Vyhledat&tt=f&changeext=0&Mask1=-1&Min1=1&Max1=60&Std1=1&beds=0&alg=1&chn=5&odch=50&odcht=0&ConnFromList=-1&ConnToList=-1&ConnViaList=-1&recalc=0&pars=0&process=0&link=%s' % (odkud2, kam2, kdy, cas, `self.CAS_URCUJE_ODJEZD`, prestup_povolen, max_prestupu, parametr_link)
    
        conn.request("POST", "/ConnForm.asp?"+self.DICT_VYHLEDAVACI_KODY2[self.TYP_SPOJE]+" HTTP/1.0", posilana_data, self.HEADERS)
    
        r = conn.getresponse()
        #print "Odpoved:", r.status, r.reason
        data = r.read()
    
        nova_adresa = r.getheader("location", "")
    
        if r.status == 200:
            #print "Nejednoznacne zadan pocatek ci cil cesty"
            
            # ulozim data jako Unicode
            self.DATA = unicode(data, self.KODOVANI_IDOS)
            conn.close()
            self.NAVRATOVY_KOD = self.KOD_NEJEDNOZNACNE_KONCOVE_BODY
            return

        elif r.status == 302 and re.search('ConnRes', nova_adresa):
            # nasel jsem spoj, zacnu vypisovat
            
            #print "Spoj nalezen"
            del self.HEADERS['Content-type']
            conn.request("GET", "/"+nova_adresa+" HTTP/1.0", '', self.HEADERS)
            
            r = conn.getresponse()
            #print "Odpoved:", r.status, r.reason
            data = r.read()
            # ukoncim spojeni
            conn.close()
            
            if re.search('ErrRes', r.getheader('location', "")):
                # zapisi do souboru spravu o chybe
                self.POPIS_CHYBY = u"Spoj vyhovující kritériím se nepodařilo nalézt (zkuste zvýšit počet přestupů) nebo došlo k nějaké jiné chybě."    
                self.NAVRATOVY_KOD = self.KOD_SPOJ_NENALEZEN
                
            else:
                # ulozim data jako Unicode
                self.DATA = unicode(data, self.KODOVANI_IDOS)
                self.NAVRATOVY_KOD = self.KOD_SPOJ_NALEZEN
         
        else:
            # zapisu do souboru chybovou hlasku
            self.POPIS_CHYBY = u"Spoj vyhovující kritériím se nepodařilo nalézt (zkuste zvýšit počet přestupů) nebo došlo k nějaké jiné chybě."
            conn.close()
            self.NAVRATOVY_KOD = self.KOD_SPOJ_NENALEZEN



    def parsuj_koncove_body(self):
        """ Parsuje html stranku a extrahuje z ni nabizene moznosti pro upresneni koncovych bodu spojeni """
        
        # zjistim co bylo spatne a naplnim pole nalezenymi moznostmi
        zpracovavana_cast = u"From"
        nenalezeno = [0,0]
        self.VYBER_ODKUD = []
        self.VYBER_KAM = []
        
        # ziskam generator radku
        gen = self.generator_dat()
        
        # ziskana data budu zpracovavat po radcich, je to tak snazsi
        # vyhozeni vyjimky StopIteration kdekoliv v cyklu znamena, ze jsem zpracoval vsechny radky
        try:
            while 1:  # cyklus ukoncim bud rucne nebo vyhozenim vyjimky

                # ziskam dalsi radek
                radek = gen.next()
            
                # zacnu vyhledavat konkretni tagy a z nich dolovat data
                # pocatek sekce s udaji o koncovych bodech spojeni
                r = re.search(u'<label for="(From|To)Stn">', radek)
                if r:            
                    zpracovavana_cast = r.group(1)
            
                if re.search(u'objekt nebyl nalezen', radek):
                    if zpracovavana_cast == u'From':
                        nenalezeno[0] = 1
                    else:                                             
                        nenalezeno[1] = 1
            
                # nalezl jsem vycet moznosti pro koncovy/cilovy bod
                r = re.search(u'<select name="(From|To)Stn"', radek)
                if r:            
                    zpracovavana_cast = r.group(1)
                
                    # dokud nenarazim na konec vyctu
                    while not re.search(u'</select>', radek):
                        radek = gen.next()    # nactu dalsi radek
                       
                        # nalezl jsem radek s polozkou vyberu
                        r = re.search(u'<option value="(.+?)".+?>(.+)</option>', radek)
                        if r:
                            pom = r.group(1).replace(u'%', u":25")
                            pom = pom.replace(u'!', u"%21")
                            pom = pom.replace(u':', u"%")

                            if zpracovavana_cast == u'From':
                                self.VYBER_ODKUD.append(r.group(2)+u":"+pom)
                            else:                                             
                                self.VYBER_KAM.append(r.group(2)+u":"+pom)
                
                    # pokud jsem na konci nabidky v casti KAM, ukoncim zpracovavani radku, je to jiz zbytecne
                    if zpracovavana_cast == u'To':
                        break

        except StopIteration:
            # prosel jsem uz vsechny radky, pouze odchytim vyjimku, aby nedoslo k ukonceni programu
            pass
        
        # pokud nektery z koncovych bodu nebyl vubec nalezen
        if nenalezeno[0]:
            self.POPIS_CHYBY += self.ODKUD+" - Objekt nenalezen\n"
            self.NAVRATOVY_KOD = self.KOD_OBJEKT_NENALEZEN
            return
        elif nenalezeno[1]:
            self.POPIS_CHYBY += self.KAM+" - Objekt nenalezen\n"
            self.NAVRATOVY_KOD = self.KOD_OBJEKT_NENALEZEN
            return
        
        # je-li seznam prazdny, vlozim alespon hledany udaj
        if len(self.VYBER_ODKUD) == 0:
            self.VYBER_ODKUD.append(self.ODKUD)
        if len(self.VYBER_KAM) == 0:
            self.VYBER_KAM.append(self.KAM)
    
    
    
    def parsuj_nalezena_spojeni(self):
        """ Parsuje html stranku s nalezenym spojenim a extrahuje z ni udaje o spojenich """
        
        pocet_spoju = 0
        self.NALEZENA_SPOJENI = []
        
        # ziskam generator radku
        gen = self.generator_dat()
        
        # ziskana data budu zpracovavat po radcich (je to tak snazsi s ohledem na predchozi funkcnost skriptu)
        # vyhozeni vyjimky StopIteration kdekoliv v cyklu znamena, ze jsem zpracoval vsechny radky
        try:
            while 1: 
          
                # ziskam dalsi radek
                radek = gen.next() 

                # hledam prvni (ci nasledujici) nalezeny spoj, kupodivu staci hledat '<tr valign="top">'
                while not re.search(u'<tr valign="top">', radek):
                    radek = gen.next()

                # najdu datum spoje
                while not re.search(u'<td align="right">', radek):
                    radek = gen.next()
                spoj_datum = self.nahrad_nechtene_retezce(self.odstran_tagy(radek)).strip()

                # najdu zastavku
                r = 0
                while not r:
                    radek = gen.next()
                    r = re.search(u'<td nowrap>(.+?)</td>', radek)
                pom_str = r.group(1).replace(u'&nbsp;',u' ')
                spoj_zastavky = re.split(u'<br>', pom_str)
                spoj_zastavky = map(self.odstran_tagy, spoj_zastavky)
                spoj_zastavky = map(self.nahrad_nechtene_retezce, spoj_zastavky)

                # najdu casy nastupu spoju
                r = 0
                while not r:
                    radek = gen.next()
                    r = re.search(u'<td align="right" nowrap>(.+)</td>', radek)
                pom_str = r.group(1).replace(u'&#160;',u'')
                spoj_vystupy = re.split(u'<br>', pom_str)
                spoj_vystupy = map(self.nahrad_nechtene_retezce, spoj_vystupy)

                # najdu vystupu spoju
                r = 0
                while not r:
                    radek = gen.next()
                    r = re.search(u'<td align="right">(.+?)</td>', radek)
                pom_str = r.group(1).replace(u'&#160;',u'')
                spoj_nastupy = re.split(u'<br>', pom_str)

                # najdu pripadne poznamky 
                r = 0
                while not r:
                    radek = gen.next()
                    r = re.search(u'<td align="right" nowrap>(.+?)</td>', radek)
                pom_str = r.group(1).replace(u'&#160;',u'')
                spoj_poznamky = re.split(u'<br>', pom_str)
                spoj_poznamky = map(self.odstran_tagy, spoj_poznamky)
                spoj_poznamky = map(self.nahrad_nechtene_retezce, spoj_poznamky)

                # hledam radek s odkazem na detaily o spoji (url na zpozdeni vlaku, url na razeni vlaku,...)
                while not re.search(u'<td nowrap align="right">', radek):
                    radek = gen.next()
                # poloha a zpozdeni vlaku
                url_poloha = ''
                r = re.search(u"<a href='(\S+)' target='_blank' title='Poloha vlaku'>", radek)
                if r:
                    url_poloha = r.group(1)
                # razeni vlaku
                url_razeni = ''
                r = re.search(u"<a href='(\S+)' target='RAZENI'", radek)
                if r:
                    url_razeni = r.group(1)

                # najdu typ spoje  (bus, vlak, pesky)
                while not re.search(u'<td nowrap>(.+?)</td>', radek):
                    radek = gen.next()
                pom_list = re.split(u'<br>', radek)
                spoj_typ_spoje = []
                spoj_cislo_spoje = []
                for pom_spoj in pom_list:
                    r = re.search(u"<a href='(Route.asp\S+)'.+?>(.+?)<", pom_spoj)
                    if r:
                        detaily_spoje = r.group(1)
                        cislo_spoje = self.nahrad_nechtene_retezce(r.group(2))
                        # pokud nemam polozku pro nazev spoje, vytvorim ji
                        if not cislo_spoje in self.DICT_URL_DETAILY_SPOJU:
                            self.DICT_URL_DETAILY_SPOJU[cislo_spoje] = {}
                        # ulozim nasbirane detaily
                        d = self.DICT_URL_DETAILY_SPOJU[cislo_spoje]
                        d["trasa"] = detaily_spoje
                        if url_poloha:
                            d["poloha"] = url_poloha
                        if url_razeni:
                            d["razeni"] = url_razeni
                    else:
                        cislo_spoje = u''
                        detaily_spoje = u''
                    spoj_cislo_spoje.append(cislo_spoje)
                    if re.search(u'bus_p.gif|Bus:', pom_spoj):
                        spoj_typ_spoje.append(u"autobus")
                    elif re.search(u'train_p.gif|Vlak:', pom_spoj):
                        spoj_typ_spoje.append(u"vlak")
                    elif re.search(u'trol_p.gif|Trol:', pom_spoj):
                        spoj_typ_spoje.append(u"trolejbus")
                    elif re.search(u'tram_p.gif|Tram:', pom_spoj):
                        spoj_typ_spoje.append(u"tramvaj")
                    elif re.search(u'metro_p.gif', pom_spoj):
                        spoj_typ_spoje.append(u"metro")
                    elif re.search(u'foot_p.gif', pom_spoj):
                        r = re.search(u'esun asi (\d+) min', pom_spoj)
                        if r:
                            spoj_typ_spoje.append(u"přesun asi "+r.group(1)+u" min")
                        else:    
                            spoj_typ_spoje.append(u"přesun pěšky")
                    else:
                        spoj_typ_spoje.append(u'')

                # najdu zaverecnou poznamku - delka cesty apod.
                r = 0
                while not r:
                    radek = gen.next()
                    r = re.search(u'<td colspan="11">(.+?)</td>', radek)
                spoj_delka_a_cena = r.group(1)
                spoj_delka_a_cena = self.nahrad_nechtene_retezce(spoj_delka_a_cena)
                    
                # sumarizuji do seznamu v poradi
                sumarizace = [spoj_datum]
                for pom_i in range(len(spoj_zastavky)):
                    spojeni_list = []
                    if pom_i<len(spoj_vystupy) and spoj_vystupy[pom_i]:
                        spojeni_list.append(string.rjust(spoj_vystupy[pom_i],5))
                    else:
                        spojeni_list.append(u"  *  ")
                    if pom_i<len(spoj_nastupy) and spoj_nastupy[pom_i]:
                        spojeni_list.append(string.rjust(spoj_nastupy[pom_i],5))
                    else:    
                        spojeni_list.append(u"  *  ")
                    spojeni_list.append(spoj_zastavky[pom_i].rstrip())
                    if pom_i<len(spoj_poznamky):
                        spojeni_list.append(spoj_poznamky[pom_i])
                    if pom_i<len(spoj_typ_spoje):
                        spojeni_list.append(spoj_typ_spoje[pom_i])
                    if pom_i<len(spoj_cislo_spoje):
                        spojeni_list.append(spoj_cislo_spoje[pom_i])
                    sumarizace.append(spojeni_list)
                
                sumarizace.append(spoj_delka_a_cena)

                self.NALEZENA_SPOJENI.append(sumarizace)

        except StopIteration:
            # prosel jsem uz vsechny radky, pouze odchytim vyjimku, aby to nevedlu k ukonceni programu
            pass

        # nyni nalezena spojeni trochu salamounsky zkratim na zadany max. pocet
        # sice bych je mohl nechat, ale v pripade, kdy chci i detaily, tak by se zbytecne hledaly i detaily ke spojum, ktere me nezajimaji
        # takhle je snazsi
        if self.CAS_URCUJE_ODJEZD:
            # v pripade ze cas uctuje odjezd, chci ty ze zacatku seznamu
            self.NALEZENA_SPOJENI = self.NALEZENA_SPOJENI[:self.MAX_SPOJU]
        else:
            # v pripade ze cas uctuje prijezd, chci ty z konce seznamu
            # v pripade ze cas uctuje odjezd, chci ty ze zacatku seznamu
            self.NALEZENA_SPOJENI = self.NALEZENA_SPOJENI[-self.MAX_SPOJU:]

    def ziskej_z_idosu_detail_spoje(self, nazev_spoje, typ):
        """ ziska z IDOSu detail spoje (autobus, vlak,..) zadaneho typu a ziskany HTML ulozi do promenne self.DATA2 """

        self.DATA2 = ''
        # pokud mam ke spoji ulozene URL na dotaz...
        if nazev_spoje in self.DICT_URL_DETAILY_SPOJU:
            url = self.DICT_URL_DETAILY_SPOJU[nazev_spoje][typ]
        else:
            # pokud ne, koncim
            return self.KOD_DETAIL_NELZE_ZISKAT
        
        # DOTAZ, chci ziskat html stranku s detaily spoje
    
        conn = httplib.HTTPConnection(self.IDOS_URL)
        conn.request("GET", '/'+url+" HTTP/1.1", '', self.HEADERS)
    
        #print "posilam dotaz"
        r = conn.getresponse()
        #print "Odpoved:", r.status, r.reason
        if r.status == 200: # "OK"
            # nactu data a ulozim je v unicode do self.DATA2
            data = r.read()
            self.DATA2 = unicode(data, self.KODOVANI_IDOS)

            return self.KOD_DETAIL_ZISKAN
        else:
            return self.KOD_DETAIL_NELZE_ZISKAT

    def parsuj_detail_spoje(self):
        """ Parsuje html stranku s detailem spoje a extrahuje z ni jednotlive zastavky """
        
        # ziskam generator radku
        gen = self.generator_dat(data = 2)
        
        # ziskana data budu zpracovavat po radcich, je to tak snazsi
        # ziskam dalsi radek
        radek = gen.next()
            
        # zacnu vyhledavat konkretni tagy a z nich dolovat data
        # pocatek sekce s udajem o cisle spojeni
        while not re.search(u"<a title='", radek):
            radek = gen.next()
        nazev = self.nahrad_nechtene_retezce(self.odstran_tagy(radek)).strip()

        # pocatek sekce se seznamem zastavek
        while not re.search(u'<td align="left" nowrap>', radek):
            radek = gen.next()
        zastavky = self.nahrad_nechtene_retezce(gen.next()).split(u'<br>')

        # sekce s casy prijezdu
        while not re.search(u'<td nowrap>', radek):
            radek = gen.next()
        prijezdy = self.nahrad_nechtene_retezce(radek[radek.find(u'>')+1:]).split(u'<br>')

        # pocatek sekce s casy odjezdu
        while not re.search(u'<td>', radek):
            radek = gen.next()
        odjezdy = self.nahrad_nechtene_retezce(radek[radek.find(u'>')+1:]).split(u'<br>')

        # pocatek sekce s poznamkami
        while not re.search(u'<td nowrap align="right">', radek):
            radek = gen.next()
        poznamky = self.nahrad_nechtene_retezce(radek[radek.find(u'>')+1:]).split(u'<br>')

        # pocatek sekce s kilometry
        while not re.search(u'<td>', radek):
            radek = gen.next()
        kilometry = self.nahrad_nechtene_retezce(radek[radek.find(u'>')+1:]).split(u'<br>')
        
        udaje = [nazev]
        
        # zpracuji jednotlive udaje
        for i in range(len(zastavky)-1):   # staci projit o 1 polozku min, to kvuli <br> na konci radku
            if zastavky[i].find(u'<b>') >=0 :  # je-li tucne, jedna se o nastupni ci vystupni zastavku - pridam na zacatek *, abych ji poznal
                zastavky[i] = u"*"+zastavky[i]
            # odstranim zbyle tagy
            udaj = map(lambda x: self.odstran_tagy(x), [zastavky[i], prijezdy[i], odjezdy[i], poznamky[i], kilometry[i]])
            # pridam ziskane udaje do seznamu
            udaje.append(udaj)

        # vratim udaje o spoji
        return udaje 



    def parsuj_zpozdeni_vlaku(self):
        """ Parsuje html stranku s detailem o pozici spoje a extrahuje z ni zpozdeni """
        # ziskam generator radku
        gen = self.generator_dat(data = 2)
        
        # ziskana data budu zpracovavat po radcich, je to tak snazsi
        # ziskam dalsi radek
        radek = gen.next()
        
        zpozdeni = ''
        # zacnu vyhledavat konkretni tagy a z nich dolovat data
        # nejdrive se posunu bliz tomu spravnemu mistu
        try:
            while not re.search(u"Informace ze stanice:", radek):
                radek = gen.next()
            # a nyni jiz na to spravne
            while not re.search(u'<td nowrap>', radek):
                radek = gen.next()
            zpozdeni = self.nahrad_nechtene_retezce(self.odstran_tagy(radek.split(u'<br>')[-1])).strip()

        # vyjimka - nenasel jsem informace v pozadovanem formatu
        except StopIteration:
            pass

        return zpozdeni



    def CLI_vypis_napovedu(self):
        """ Program vypise napovedu pro pouziti v CLI """
        
        print """
Skript hleda dopravni spoje prostrednictvim serveru vlaky.cz
Verze 0.6, http://code.google.com/p/spoje/

Pouziti:  spoje.py [prepinace] typ_spoje odkud[:kod] kam[:kod]

Argumenty:
    typ_spoje  jedna z nasledujicich moznosti:
                 vlak - vlakova spojeni v CR
                 bus - autobusove spoje v CR
                 komb - autobusove a vlakove spoje v CR
                 brno - MHD v Brne (vcetne IDS JMK) 
                 praha - MHD v Praze
                 ostrava - MHD v Ostrave
                 liberec - MHD v Liberci
    odkud      Retezec urcujici misto (zastavku) odjezdu. Viceslovny 
               nazev je treba (spolu s pripadnym kodem) uzavrit do 
               uvozovek nebo apostrofu.
    kam        Retezec urcujici misto (zastavku) prijezdu. Viceslovny 
               nazev je treba (spolu s pripadnym kodem) uzavrit do 
               uvozovek nebo apostrofu.
    kod        Retezec identifikujici misto v pripade nejednoznacneho 
               zadani.

Prepinace:
    -b         Batch mode - nepta se na pripadne upresneni spoje.
    -c cas     Cas odjezdu resp. prijezdu (do cilove stanice) 
               hledaneho spojeni (defaultni hodnotou je aktualni cas).
               Cas odjezdu specifikujeme napriklad '-c 10:00'.
               Cas prijezdu se specifikuje pomoci znaku 'p' hned za 
               zadanym casem, tedy napriklad '-c 10:00p' oznacuje 
               spojeni s casem prijezdu pred 10:00.
    -d datum   Datum odjezdu/prijezdu (defaultni hodnotou je aktualni 
               datum), napriklad '-d 25.7.' nebo '-d 25.7.2008'.
               Pri neuvedeni roku se pouzije aktualni kalendarni rok.
    -p cislo   Maximalni pocet prestupu (defaultni hodnota 3)
    -s cislo   Pocet hledanych spoju (defaultni hodnota 5)
    -t         U kazdeho spoje vypise zastavky na hledane trase 
    -T         U kazdeho spoje vypise zastavky na cele jeho trase
    -z         Dohledani informace o zpozdeni vlaku
    """

    

    def CLI_vyber_z_menu(self, option_list, otazka=u"Upřesněte výběr", prompt=u'Vaše volba: '):
        """ Vypise dialog pro vyber z nabizenych moznosti a vraci cislo vybrane polozky """

        print otazka.encode(self.KODOVANI_SYSTEM)
        n = len(option_list)
        for i in range(n):
            print `i+1`+") "+option_list[i].split(":",1)[0].encode(self.KODOVANI_SYSTEM)
        c = 0
        while c not in range(1,n+1):
            c = raw_input(prompt.encode(self.KODOVANI_SYSTEM))
            if c.isdigit():
                c = int(c)
            else:
                c = 0
            print 
        return c-1




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

    def parseIdosOutput(self, spojeni):
        ret = []
        for item in spojeni:
            date = self.convertDate(item[0])
            detail = item[-1]
            conn = Connection([], detail)
            for i1, i2 in bigramIter(item[1:-1]):
                fromStation = i1[2]
                toStation = i2[2]
                fromTime = self.convertTime(i1[1])
                toTime = self.convertTime(i2[0])
                type = i1[4]
                part = ConnectionPart(fromStation, fromTime, toStation, toTime, date, type)
                conn.append(part)
            ret.append(conn)
        return ret

    def idosFind(self, time, departureTime):
        time_s = time.strftime('%H:%M')
        if self.date is not None:
            date_s = self.date.strftime('%d.%m.%Y')
        else:
            current_time = time_m.localtime()
            date_s = datetime.date(*current_time[:3]).strftime('%d.%m.%Y')

        idos = IDOS()
        idos.ODKUD = self.fromStation
        idos.KAM = self.toStation
        idos.KDY = date_s
        idos.CAS = time_s
        idos.CAS_URCUJE_ODJEZD = departureTime

        idos.vyhledej_dopravni_spojeni()

        return self.parseIdosOutput(idos.NALEZENA_SPOJENI)




if __name__ == '__main__':
    lst = ConnectionList(u'Plzen', u'Pisek', datetime.time(8, 00), datetime.date(2008, 12, 7), departureTime=False)
    for i in range(20):
        print lst.next()
    for i in range(30):
        print lst.prev()
    for i in range(50):
        print lst.next()
