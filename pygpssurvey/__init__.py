# -*- coding: utf-8 -*-
'''
    pygpssurvey
    -----------

    The public API and command-line interface to PyGPSSurvey package.

    :copyright: Copyright 2018 Lionel Darras and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
# Make sure the logger is configured early:
from .logger import LOGGER, active_logger
from .device import GPSSurvey

VERSION = '0.1dev'
__version__ = VERSION
