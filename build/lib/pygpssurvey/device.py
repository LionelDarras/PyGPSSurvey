# -*- coding: utf-8 -*-
'''
    pygpssurvey.device
    ------------------

    Position and implantation tools using GPS system boards via NMEA frames

    :copyright: Copyright 2018 Lionel Darras and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import division, unicode_literals
import msvcrt
import time
import pynmea2
import utm
from pylink import link_from_url

from .logger import LOGGER
from .utils import (cached_property, retry, bytes_to_hex, hex_to_bytes,
                    ListDict, is_bytes)
from .compat import stdout


class NoDeviceException(Exception):
    '''Can not access device.'''
    value = __doc__


class BadCmdException(Exception):
    '''No valid command.'''
    value = __doc__


class BadAckException(Exception):
    '''No valid acknowledgement.'''
    def __str__(self):
        return self.__doc__


class BadCRCException(Exception):
    '''No valid checksum.'''
    def __str__(self):
        return self.__doc__


class BadDataException(Exception):
    '''No valid data.'''
    def __str__(self):
        return self.__doc__


class GPSSurvey(object):
    '''Communicates with the board by sending commands, reads the binary
    data and parsing it into usable scalar values.

    :param link: A `PyLink` connection.
    '''
    
    def __init__(self, link):
        self.link = link
        self.link.open()
        self.recframe=[]    # reception frame empty

    @classmethod
    def from_url(cls, url, timeout=10):
        ''' Get device from url.

        :param url: A `PyLink` connection URL.
        :param timeout: Set a read timeout value.
        '''
        link = link_from_url(url)
        link.settimeout(timeout)
        return cls(link)

    def updatereceptionframe(self, size=None, timeout=None):
        ''' update reception frame by getting bytes received.
        The maximum amount of data to be received at once
        is specified by `size`.
        '''
        bytes = self.link.read(size=size, timeout=timeout)
        if (len(bytes) > 0):
            for l in range(len(bytes)):
                self.recframe.append(bytes[l])
        try:
            nmeaframe = pynmea2.parse(bytes)
        except:
            nmeaframe = None
        return nmeaframe
        
    def getpointsposition(self, output, rawoutput, delim=";", stdoutdisplay=False, measuresnb=10, pointfixfilter=False, pointnamememory=False, dir=""):
        ''' Get points position

        :param output: Filename where output is written
        :param delim: CSV char delimiter (default: ";")
        :param stdoutdisplay: Display on the standard out if defined output is a file        
        :param measuresnb: Number of measurements to do obtain a mean point (default: 10)        
        :param pointnamememory: Memorise a specified point name (default: False)
        :param dir: Directory where output is written (default: "")
        '''

        samplesnb = 0
        pointnum = 1
        pointname = ""
        output.write('pointnum' + delim + 'pointname' + delim + 'lon' + delim + 'lon_dir' + delim + 'lat' + delim + 'lat_dir' + delim + 'alt' + delim + 'alt_units' + '\n')
        key = '&'
        if (pointfixfilter == True):
            gps_qual_min = 1
        else :
            gps_qual_min = 0
               
        while ((ord(key) != ord('Q')) and (ord(key) != ord('q'))):
            try:
                nmeaframe = self.updatereceptionframe(None,0.1)                             # update reception frame if needed
                if (stdoutdisplay == True) and (nmeaframe!=None):
                    stdout.write(str(nmeaframe) + '\n')
                            
                if msvcrt.kbhit():                                              # key press detection
                    key = msvcrt.getch()
                    if (ord(key) == ord('M')) or (ord(key) == ord('m')):                                            # to memorise GPS point
                        if (stdoutdisplay == True):
                            stdout.write('begin saving mean point position ' + str(pointnum) + '\n')
                        measuresnbtodo = measuresnb
                        rawoutput.write(str(pointnum) + '\n')
                        longitudetab = []
                        latitudetab = []
                        altitudetab = []
                        while (measuresnbtodo > 0): # et time out de 5xmeasuresnb non dépassé
                            nmeaframe = self.updatereceptionframe(None,0.1)                             # update reception frame if needed
                            try:
                                if (nmeaframe.gps_qual > gps_qual_min):                                
                                    rawoutput.write(str(nmeaframe) + '\n')
                                    if (stdoutdisplay == True):
                                        stdout.write(str(nmeaframe) + '\n')
                                    if (int(nmeaframe.gps_qual) > 0):
                                        longitudetab.append(float(nmeaframe.longitude))
                                        latitudetab.append(float(nmeaframe.latitude))
                                        altitudetab.append(float(nmeaframe.altitude))
                                        measuresnbtodo -= 1
                            except:
                                pass
                        if (stdoutdisplay == True):
                            stdout.write('end saving mean point position ' + str(pointnum) + '\n')
                        output.write(str(pointnum) + delim + pointname + delim + str(sum(longitudetab)/len(longitudetab)) + delim + nmeaframe.lon_dir + delim + str(sum(latitudetab)/len(latitudetab)) + delim + nmeaframe.lat_dir + delim + str(sum(altitudetab)/len(altitudetab)) + delim + nmeaframe.altitude_units + '\n')
                        pointnum += 1

                    elif (ord(key) == ord('D')) or (ord(key) == ord('d')):                                          # to delete last GPS point
                        # effacement de la dernière ligne (donc dernier point)
                        print('D')

            except KeyboardInterrupt:                                           # 'Ctrl' + 'C' detected
                break            
        
    def setpointsimplantation(self, output, rawoutput, input, delim=";", stdoutdisplay=False, measuresnb=10, pointfixfilter=False, pointnamememory=False, utmzoneletter=None, utmzonenumber=0, dir=""):
        ''' Get points position

        :param output: Filename where output is written
        :param input: Filename where input is read (default: "input.txt")
        :param delim: CSV char delimiter (default: ";")
        :param stdoutdisplay: Display on the standard out if defined output is a file        
        :param measuresnb: Number of measurements to do obtain a mean point (default: 10)        
        :param pointnamememorize: Memorise a specified point name (default: False)
        :param utmzoneletter: UTM zone letter (default: None)
        :param utmzonenumber: UTM zone number (default: 0)
        :param dir: Directory where output is written (default: "")
        '''

        samplesnb = 0
        pointnum = 1
        pointname = ""
        index_ref = 1
        pointslist = self.pointslist(input, delim)
        if (len(pointslist)<2):
            lon_ref = None
            lat_ref = None
        else:
            num_ref = pointslist[index_ref][0]
            lon_ref = pointslist[index_ref][2]
            lat_ref = pointslist[index_ref][4]
                    
        output.write('pointnum' + delim + 'pointname' + delim + 'lon' + delim + 'lon_dir' + delim + 'lat' + delim + 'lat_dir' + delim + 'alt' + delim + 'alt_units' + '\n')
        key = '&'
        if (pointfixfilter == True):
            gps_qual_min = 1
        else :
            gps_qual_min = 0
               
        while ((ord(key) != ord('Q')) and (ord(key) != ord('q'))):
            try:
                nmeaframe = self.updatereceptionframe(None,0.1)                             # update reception frame if needed
                if (stdoutdisplay == True) and (nmeaframe!=None):
                    if ((lon_ref == None) or (lat_ref == None)):
                        stdout.write(str(nmeaframe) + '\n')
                    else:
                        if (utmzoneletter == None):
                            lon_gap = str(float(nmeaframe.longitude)-float(lon_ref))
                            lat_gap = str(float(nmeaframe.latitude)-float(lat_ref))
                        else:
                            lat_utm, lon_utm, zonenumber_utm, zoneletter_utm = utm.from_latlon(nmeaframe.latitude,nmeaframe.longitude)
                            lat_ref_utm, lon_ref_utm, zonenumber_utm, zoneletter_utm = utm.from_latlon(float(lat_ref),float(lon_ref))
                            lon_gap = lon_utm - lon_ref_utm
                            lat_gap = lat_utm - lat_ref_utm
                        stdout.write(num_ref + ',' + lon_ref + ',' + lat_ref + ',' + str(lon_gap) + ',' + str(lat_gap) + '\n')
                            
                if msvcrt.kbhit():                                              # key press detection
                    key = msvcrt.getch()
                    if (ord(key) == ord('M')) or (ord(key) == ord('m')):                                            # to memorise GPS point
                        if (stdoutdisplay == True):
                            stdout.write('begin saving mean point position ' + str(pointnum) + '\n')
                        measuresnbtodo = measuresnb
                        rawoutput.write(str(pointnum) + '\n')
                        longitudetab = []
                        latitudetab = []
                        altitudetab = []
                        while (measuresnbtodo > 0): # et time out de 5xmeasuresnb non dépassé
                            nmeaframe = self.updatereceptionframe(None,0.1)                             # update reception frame if needed
                            try:
                                if (nmeaframe.gps_qual > gps_qual_min):                                
                                    rawoutput.write(str(nmeaframe) + '\n')
                                    if (stdoutdisplay == True):
                                        stdout.write(str(nmeaframe) + '\n')
                                    if (int(nmeaframe.gps_qual) > 0):
                                        longitudetab.append(float(nmeaframe.longitude))
                                        latitudetab.append(float(nmeaframe.latitude))
                                        altitudetab.append(float(nmeaframe.altitude))
                                        measuresnbtodo -= 1
                            except:
                                pass
                        if (stdoutdisplay == True):
                            stdout.write('end saving mean point position ' + str(pointnum) + '\n')
                        output.write(str(pointnum) + delim + pointname + delim + str(sum(longitudetab)/len(longitudetab)) + delim + nmeaframe.lon_dir + delim + str(sum(latitudetab)/len(latitudetab)) + delim + nmeaframe.lat_dir + delim + str(sum(altitudetab)/len(altitudetab)) + delim + nmeaframe.altitude_units + '\n')
                        pointnum += 1

                    elif (ord(key) == ord('D')) or (ord(key) == ord('d')):                                          # to delete last GPS point
                        # effacement de la dernière ligne (donc dernier point)
                        print('D')
                    elif (ord(key) == ord('P')) or (ord(key) == ord('p')):                                          # to find previous GPS point
                        if (len(pointslist) > 2):
                            if (index_ref > 1):
                                index_ref -= 1
                            else:
                                index_ref = len(pointslist) - 1
                            num_ref = pointslist[index_ref][0]
                            lon_ref = pointslist[index_ref][2]
                            lat_ref = pointslist[index_ref][4]
                    elif (ord(key) == ord('N')) or (ord(key) == ord('n')):                                          # to find next GPS point
                        if (len(pointslist) > 2):
                            if (index_ref < (len(pointslist) - 1)):
                                index_ref += 1
                            else:
                                index_ref = 1
                            num_ref = pointslist[index_ref][0]
                            lon_ref = pointslist[index_ref][2]
                            lat_ref = pointslist[index_ref][4]
                    elif (ord(key) == ord('L')) or (ord(key) == ord('l')):                                          # to list GPS points
                        stdout.write('\n')
                        for i in range(len(pointslist)):
                            for j in range(len(pointslist[i])):
                                if (j != 0):
                                    stdout.write(',')
                                stdout.write(pointslist[i][j])
                        stdout.write('\n')
            except KeyboardInterrupt:                                           # 'Ctrl' + 'C' detected
                break            

    def pointslist(self, input, delim):
        list=[]
        lines = input.readlines()
        for line in lines:
            list.append(line.split(delim))
        return list