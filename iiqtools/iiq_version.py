# -*- coding: UTF-8 -*-
"""
This module contains the business logic for print the versions of InsightIQ
and IIQTool that's installed.
"""
from __future__ import print_function # so we can mock it away in tests
import argparse

from iiqtools.utils import versions


def parse_cli(the_cli_args):
    """Defines the CLI interface for ``iiq_version``"""
    parser = argparse.ArgumentParser(description='Display the versions of InsightIQ and IIQTools',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    args = parser.parse_args(the_cli_args)
    return args


def main(the_cli_args):
    """Entry point for iiq_version script"""
    # Really is here just to support -h/--help
    parse_cli(the_cli_args)

    iiqtools_version = versions.get_iiqtools_version()
    insightiq_version = versions.get_iiq_version()
    print('InsightIQ: %s' % getattr(insightiq_version, 'version', 'None'))
    print('IIQTools: %s' % getattr(iiqtools_version, 'version', 'None'))
