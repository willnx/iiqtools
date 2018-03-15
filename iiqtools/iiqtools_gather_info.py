# -*- coding: UTF-8 -*-
"""
This module contains all the business logic for collecting logs and configuration
information about InsightIQ for remote troubleshooting.
"""
import os
import sys
import time
import json
import glob
import tarfile
import argparse
import traceback
import subprocess
from getpass import getuser
from StringIO import StringIO

try:
    from iiq_data_export.api_connection import iiq_api
    from insightiq.lib.api_connection.api import APIConnectionError
except ImportError:
    # InsightIQ is closed source, so it cannot be included as a dev/test dependency.
    # We're stuck with assuming a dev/test environment, and mocking it away.
    # This is the only way we can do unit testing, and yes, it's a bit hacky.
    from mock import MagicMock
    iiq_api = MagicMock()
    APIConnectionError = RuntimeError

from iiqtools.utils import versions
from iiqtools.utils import cli_parsers
from iiqtools.utils.logger import get_logger
from iiqtools.utils.generic import check_path
from iiqtools.utils.shell import run_cmd
from iiqtools.exceptions import CliError


def get_tarfile(output_dir, case_number, the_time=None):
    """Centralizes logic for making tgz file for InsightIQ logs

    :Returns: tarfile.TarFile

    :param output_dir: **Required** The directory to save the tar file in
    :type output_dir: String

    :param case_number: **Required** The SR that the logs are for; used in file name.
    :type case_number: String or Integer

    :param the_time: An optional EPOC timestamp to use when naming the file.
                     If not supplied, this function calls time.time().
    :type the_time: EPOC time stamp
    """
    base_dir = os.path.abspath(output_dir)
    if the_time is None:
        the_time = int(time.time())
    file_name = 'IIQLogs-sr%s-%s.tgz' % (case_number, the_time)
    full_path = os.path.join(base_dir, file_name)
    return tarfile.open(full_path, 'w:gz') # 2nd param makes it a tgz file


def add_from_memory(the_tarfile, data_name, data):
    """Simplify adding in-memory information to the tar file

    :Returns: None

    :param the_tarfile: The open tarfile object
    :type the_tarfile: tarfile.open

    :param data_name: The reference to the data; i.e. it's name when you uncompress the file
    :type data_name: String

    :param data: The contents of the in-memory information
    :type data: String
    """
    info = tarfile.TarInfo(data_name)
    info.size = len(data)
    info.mtime = time.time()
    info.mode = int('444', 8) # everyone can read in oct, not decimal
    the_tarfile.addfile(info, StringIO(data))


def parse_cli(cli_args):
    """Handles parsing the CLI, and gives us --help for (basically) free

    :Returns: argparse.Namespace

    :param cli_args: The arguments passed to the script
    :type cli_args: List
    """
    parser = argparse.ArgumentParser(description='Generate a .tar file for debugging InsightIQ',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--output-dir', default='/home/administrator', type=check_path,
        help='The directory to write the .tgz file to')
    parser.add_argument('--case-number', required=True,
        help='The Service Request number. Used in naming tar file.')

    args = parser.parse_args(cli_args)
    return args


# IIQ API info
def call_iiq_api(uri):
    """Make an internal API call to the InsightIQ API

    :Returns: JSON String

    :param uri: The API end point to call
    :type uri: string
    """
    template = {'category' : 'api',
                'endpoint' : uri,
                'error' : '',
                'response' : None,
                'traceback' : ''}
    try:
        resp = iiq_api.make_request(uri)
    except APIConnectionError:
        template['error'] = "unable to query InsightIQ API"
    except Exception as doh:
        template['error'] = "%s" % doh
        template['traceback'] = traceback.format_exc()
    else:
        data = json.loads(resp.read())
        template['response'] = data

    # The indent makes the JSON more human friendly, which GS appreciates
    return json.dumps(template, indent=4, sort_keys=True)


def datastore_info():
    """Obtain data about the datastore for InsightIQ

    :Returns: JSON String
    """
    return call_iiq_api('/api/datastore/usage?current_dir=true')


def clusters_info():
    """Obtain a pile of data about all monitored clusters in InsightIQ

    :Returns: JSON String
    """
    return call_iiq_api('/api/clusters')


def ldap_info():
    """Obtain the config for LDAP in InsightIQ

    :Returns: JSON String
    """
    return call_iiq_api('/api/ldap/configs')


def reports_info():
    """Obtain info about any scheduled reports in InsightIQ

    :Returns: JSON String
    """
    return call_iiq_api('/api/reports')


# CLI command info
def cli_cmd_info(command, parser):
    """Standardizes the JSON format for any data collected via a CLI command

    :Returns: JSON String

    :param command: The CLI command to execute
    :type command: String
    """
    try:
        result = run_cmd(command)
    except CliError as result:
        pass
    template = {'exitcode' : result.exit_code,
                'stderr' : result.stderr,
                'command' : result.command,
                'stdout' : result.stdout,
                'category' : 'cli',
                'traceback' : ''}
    if not (result.exit_code or result.stderr):
        # I know, shitty heuristic to determine errors...
        try:
            parsed_format = parser(result.stdout)
        except Exception:
            template['traceback'] = traceback.format_exc()
        else:
            template.update(parsed_format)

    return json.dumps(template, indent=4, sort_keys=True)


def mount_info():
    """Obtain data about mounted file systems on the host OS

    :Returns: JSON String
    """
    return cli_cmd_info('df -P', cli_parsers.df_to_dict)


def memory_info():
    """Obtain data about RAM on the host OS

    :Returns: JSON String
    """
    return cli_cmd_info('free -m', cli_parsers.memory_to_dict)


def ifconfig_info():
    """Obtain data about the network interfaces on the host OS

    :Returns: JSON String
    """
    return cli_cmd_info('ifconfig', cli_parsers.ifconfig_to_dict)


def iiq_version_info():
    """Obtain info about the version of InsightIQ installed on the host OS

    :Returns: JSON String
    """
    iiq_version = versions.get_iiq_version()
    iiqtools_version = versions.get_iiqtools_version()
    data = {'insightiq' : iiq_version.version,  'iiqtools' : iiqtools_version.version}
    return json.dumps(data, indent=4, sort_keys=True)


def main(the_cli_args):
    """Entry point for running script"""
    args = parse_cli(the_cli_args)
    user = getuser()
    if user != 'root':
        warning = '\n****WARNING****\nNot all data is going to be collected because\n'
        warning += 'some log files can only be read by root.\n'
        warning += 'To collect all diagnostic data, you must run as root.\n'
        warning += 'You are currently running as %s\n' % user
        print(warning)
        response = raw_input('Do you wish to continue? (yes/no): ')
        if not response.lower().startswith('y'):
            return 1

    log = get_logger(log_path='/dev/null', stream_lvl=10, file_lvl=10)
    try:
        tar_file = get_tarfile(args.output_dir, args.case_number)
    except (IOError, OSError) as doh:
        log.error(doh)
        return doh.errno

    log.info('Collecting config information')
    add_from_memory(tar_file, 'iiq_version.json', iiq_version_info())
    add_from_memory(tar_file, 'ifconfig.json', ifconfig_info())
    add_from_memory(tar_file, 'memory.json', memory_info())
    add_from_memory(tar_file, 'df.json', mount_info())

    add_from_memory(tar_file, 'ldap.json', ldap_info())
    add_from_memory(tar_file, 'clusters.json', clusters_info())
    add_from_memory(tar_file, 'datastore.json', datastore_info())

    # add release info files
    for releaseinfo in glob.glob('/etc/*release'):
        tar_file.add(releaseinfo)

    # add config files
    for a_file in glob.glob('/etc/isilon/*'):
        tar_file.add(a_file)
    for rabbitconfig in glob.glob('/etc/rabbitmq/*.config'):
        tar_file.add(rabbitconfig)

    log.info('Collecting log files')
    # add iiq log files
    for iiq_log in glob.glob('/var/log/insightiq*'):
        tar_file.add(iiq_log)
    for iiq_log in glob.glob('/var/log/iiq*'):
        tar_file.add(iiq_log)
    for iiq_log in glob.glob('/var/log/insightiq_clusters/*/*'):
        tar_file.add(iiq_log)

    # add postgres logs
    try:
        tar_file.add('/var/cache/insightiq/pgsql/pgstartup.log')
    except (IOError, OSError):
        # It's a permissions error; already prompted user that not all files
        # can be collected if not ran as root
        pass
    for pglog in glob.glob('/var/log/pg_log/*'):
        tar_file.add(pglog)

    # add rabbitmq logs
    for rabbitlog in glob.glob('/var/log/rabbitmq/*'):
        tar_file.add(rabbitlog)

    tar_file.close()
    log.info('Log gather complete')
    log.info('Created log file %s', tar_file.name)
    return 0
