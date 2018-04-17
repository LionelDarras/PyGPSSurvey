# -*- coding: utf-8 -*-
'''
    pygpssurvey
    -----------

    The public API and command-line interface to PyGPSSurvey package.

    :copyright: Copyright 2018 Lionel Darras and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
import os
import argparse
import time
import copy
from datetime import datetime

# Make sure the logger is configured early:
from . import VERSION
from .logger import active_logger
from .device import GPSSurvey
from .compat import stdout


def setstdcmd(cmdtype, device):
    '''set standard command'''
    fields = device.setcmd(cmdtype)
    for i in range(len(fields)):
        if fields[i]['name'] != 'reserved':
            stdout.write(("%s : " + fields[i]['valuefmt'] + "\n")%(fields[i]['name'],fields[i]['value']))


def getpointsposition_cmd(args, device):
    '''Getpointsposition command.'''
    device.getpointsposition(args.output, args.rawoutput, delim=args.delim, stdoutdisplay=args.stdoutdisplay, measuresnb=args.measuresnb, pointfixfilter=args.pointfixfilter, pointnamememory=args.pointnamememory)


def setpointsimplantation_cmd(args, device):
    '''Setpointsimplantation command.'''
    device.setpointsimplantation(args.output, args.rawoutput, args.input, delim=args.delim, stdoutdisplay=args.stdoutdisplay, measuresnb=args.measuresnb, pointfixfilter=args.pointfixfilter, pointnamememory=args.pointnamememory, utmzoneletter=args.utmzoneletter, utmzonenumber=args.utmzonenumber)


def get_cmd_parser(cmd, subparsers, help, func):
    '''Make a subparser command.'''
    parser = subparsers.add_parser(cmd, help=help, description=help)
    parser.add_argument('--timeout', default=10.0, type=float,
                        help="Connection link timeout")
    parser.add_argument('--debug', action="store_true", default=False,
                        help='Display log')
    parser.add_argument('url', action="store",
                        help="Specify URL for connection link. "
                             "E.g. tcp:iphost:port "
                             "or serial:/dev/ttyUSB0:19200:8N1")
    parser.set_defaults(func=func)
    return parser


def main():
    '''Parse command-line arguments and execute GPSSurvey command.'''

    parser = argparse.ArgumentParser(prog='pygpssurvey',
                                     description='Position and implantation '
                                                 'tools using GPS system boards '
                                                 'via NMEA frames')
    parser.add_argument('--version', action='version',
                         version='PyGPSSurvey version %s' % VERSION,
                         help='Print PyGPSSurvey version number and exit.')

    subparsers = parser.add_subparsers(title='The PyGPSSurvey commands')
    # getpointsposition command
    subparser = get_cmd_parser('getpointsposition', subparsers,
                               help='Get GPS points position.',
                               func=getpointsposition_cmd)
    subparser.add_argument('output', action='store',
                           type=argparse.FileType('w'),
                           help='Filename where GPS points to locate are written')
    subparser.add_argument('--rawoutput', action='store', default="rawoutput.txt",
                           type=argparse.FileType('w'),
                           help='Filename where raw NMEA frames of GPS points to locate are written (default: "rawoutput.txt"')
    subparser.add_argument('--delim', action="store", default=";",
                           help='CSV char delimiter (default: ";"')
    subparser.add_argument('--stdoutdisplay', action="store_true", default=False,
                           help='Display on the standard out if defined output is a file')
    subparser.add_argument('--measuresnb', default=10, type=int,
                        help="Number of measurements to do obtain a mean point")
    subparser.add_argument('--dir', action="store", default="",
                           help='Directory where output is written (default: ""')
    subparser.add_argument('--pointfixfilter', action="store_true", default=False,
                           help='Do not add the point located in Fix GPS (Fix Qualification = 1) ')
    subparser.add_argument('--pointnamememory', action="store_true", default=False,
                           help='Memorise a specified point name')
        
    # setpointsimplantation command
    subparser = get_cmd_parser('setpointsimplantation', subparsers,
                               help='Implant GPS points.',
                               func=setpointsimplantation_cmd)
    subparser.add_argument('output', action='store',
                           type=argparse.FileType('w'),
                           help='Filename where GPS points to locate are written')
    subparser.add_argument('--input', action='store', default="input.txt",
                           type=argparse.FileType('r'),
                           help='Filename where GPS points to implant are read')
    subparser.add_argument('--rawoutput', action='store', default="rawoutput.txt",
                           type=argparse.FileType('w'),
                           help='Filename where raw NMEA frames of GPS points to locate are written (default: "rawoutput.txt"')
    subparser.add_argument('--delim', action="store", default=";",
                           help='CSV char delimiter (default: ";"')
    subparser.add_argument('--stdoutdisplay', action="store_true", default=False,
                           help='Display on the standard out if defined output is a file')
    subparser.add_argument('--measuresnb', default=10, type=int,
                        help="Number of measurements to do obtain a mean point")
    subparser.add_argument('--dir', action="store", default="",
                           help='Directory where output is written (default: ""')
    subparser.add_argument('--pointfixfilter', action="store_true", default=False,
                           help='Do not add the point located in Fix GPS (Fix Qualification = 1) ')
    subparser.add_argument('--pointnamememory', action="store_true", default=False,
                           help='Memorise a specified point name')
    subparser.add_argument('--utmzoneletter', action="store", default=None,
                           help='UTM zone letter')
    subparser.add_argument('--utmzonenumber', default=0, type=int,
                           help='UTM zone number')
        
    # Parse argv arguments
    try:
        args = parser.parse_args()
        try:            
            if args.func:
                isfunc = True
        except:
            isfunc = False

        if (isfunc == True):
            if args.debug:
                active_logger()
                device = GPSSurvey.from_url(args.url, args.timeout)
                args.func(args, device)
            else:
                try:                
                    device = GPSSurvey.from_url(args.url, args.timeout)
                    args.func(args, device)
                except Exception as e:
                    parser.error('%s' % e)
        else:
            parser.error("No command")

                    
    except Exception as e:
        parser.error('%s' % e)
        

if __name__ == '__main__':
    main()
