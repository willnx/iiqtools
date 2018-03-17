# -*- coding: UTF-8 -*-
# Path-hacking this file to enable IIQTools to import any python module
# used by InsightIQ. Adding the path-hack to this file because Python will
# execute the below code before attempting to import dependencies in modules
# below `iiqtools` directory.
import sys

sys.path.insert(1, '/usr/share/isilon/lib/python2.7/site-packages')
