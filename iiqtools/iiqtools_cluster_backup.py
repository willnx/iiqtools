# -*- coding: UTF-8 -*-
"""
This module contains all the business logic for creating an archive backup
of OneFS cluster data within InsightIQ.
"""
from __future__ import print_function
import re
import os
import json
import zipfile
import getpass
import argparse

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

from iiqtools.utils.generic import printerr
from iiqtools.utils.insightiq_api import InsightiqApi, Parameters, ConnectionError


def is_backup_file(value):
    msg = None
    regex = re.compile("^insightiq_export_\d{10}.zip")
    if not os.path.isfile(value):
        msg = 'Supplied file does not exist: %s' % value
    elif not zipfile.is_zipfile(value):
        msg = 'Supplied file is not in zip format: %s' % value
    elif not regex.search(os.path.basename(value)):
        msg = 'Supplied file is not a valid InsightIQ backup file'

    if msg is None:
        return value
    else:
        raise argparse.ArgumentTypeError(msg)


def parse_args(cli_args):
    """Parse the CLI arguments into usable a object

    :Returns: argparse.Namespace

    :param cli_args: **Required** The CLI arguments
    :type cli_args: List
    """
    parser = argparse.ArgumentParser(description='Create a backup archive of cluster statistics',
                usage="iiq_cluster_backup [-h] (--show-clusters | --clusters CLUSTERS [CLUSTERS ...]  "
                      "--username USERNAME --password PASSWORD --location LOCATION)")

    mutually_exclusive = parser.add_mutually_exclusive_group(required=True)
    mutually_exclusive.add_argument('-s', '--show-clusters', action='store_true',
        help='A list of clusters that can be backed up')
    mutually_exclusive.add_argument('-c', '--clusters', nargs='+', # at least one value required,
        help='The cluster(s) to back up')
    mutually_exclusive.add_argument('-a', '--all-clusters', action='store_true',
        help='Backup all clusters configured within InsightIQ')
    mutually_exclusive.add_argument('-i', '--inspect', type=is_backup_file,
        help='List the contents within an existing backup file')

    parser.add_argument('-l', '--location',
        help='The NFS mount or local file system location to save the archive file to')
    parser.add_argument('-u', '--username',
        help='The Administrative user to authenticate as')
    parser.add_argument('-p', '--password',
        help="The Administrative user's password. If not supplied, you will be "
              "prompted for it; this avoids leaving the password in your shell history")
    parser.add_argument('-m', '--max-backups', type=int, default=0,
        help="The maximum number of backups (count) to retain before starting a new job."
             "A value of zero means *never* delete old backups")

    args = parser.parse_args(cli_args)
    if args.clusters or args.all_clusters:
        if not (args.location and args.username):
            parser.error('-l/--location and --username required')
        if not args.password:
            args.password = getpass.getpass('Please enter the password for %s :' % args.username)
    return args


def get_clusters_in_iiq():
    """Obtain a list of clusters and their GUIDs from InsightIQ

    :Returns: Dictionary - Cluster Name -> Cluster GUID
    """
    response = iiq_api.make_request('/api/clusters')
    clusters_verbose = json.loads(response.read())
    clusters_basic = {}
    for cluster in clusters_verbose['clusters']:
        clusters_basic[cluster['name']] = cluster['guid']
    return clusters_basic


def format_cluster_output(clusters):
    """Format the dictionary of clusters into CLI friendly output

    :Returns: String

    :param clusters: **Required** A mapping of cluster names to GUIDs
    :type clusters: Dictionary
    """
    pretty_output = '\nClusters monitored by InsightIQ\n%s\n\n' % ('-' * 31)
    formatted_clusters = '\n  '.join(clusters.keys())
    return pretty_output + '  ' + formatted_clusters


def supplied_clusters_ok(supplied_clusters, available_clusters):
    """User input validation; ensure requested clusters are monitored by InsightIQ

    The point of this function is to pull the business logic out of the main
    function, and not require I/O to exercise it. This increases the unit testability
    of the script.

    :Returns: Boolean

    :param supplied_clusters: **Required** The user requested clusters to backup
    :type supplied_clusters: List

    :param availble_clusters: **Required** The clusters currently monitored by IIQ
    :type available_clusters: List
    """
    return set(supplied_clusters) <= set(available_clusters)


def _make_export_params(supplied_clusters, available_clusters, location):
    """Convert the user supplied values into the API parameters for InsightIQ

    :Returns: String

    :param supplied_clusters: **Required** The user requested clusters to backup
    :type supplied_clusters: List

    :param availble_clusters: **Required** The clusters currently monitored by IIQ
    :type available_clusters: Dictionary

    :param location: **Required** Where the export files should be saved. A colon
                     in this value indicates the location is on an NFS export.
    :type location: String
    """
    params = Parameters()
    if ":" in location:
        nfs_host, filesystem_location = location.split(':')
    else:
        filesystem_location = location
        nfs_host = ''

    params.add(name='nfs_host', value=nfs_host)
    params.add(name='location', value=filesystem_location)

    for cluster in supplied_clusters:
        params.add(name='guid', value=available_clusters[cluster])

    return params


def export_via_api(supplied_clusters, available_clusters, location, username, password):
    """Call the InsightIQ API to kick off the cluster backup archive process

    :Raises: ValueError when API response is not JSON

    :param supplied_clusters: **Required** The user requested clusters to backup
    :type supplied_clusters: List

    :param availble_clusters: **Required** The clusters currently monitored by IIQ
    :type available_clusters: List

    :param location: **Required** Where the export files should be saved. A colon
                     in this value indicates the location is on an NFS export.
    :type location: String

    :param username: **Required** An administrative user in InsightIQ
    :type username: String

    :param password: **Required** The credential for the administrative user
    :type password: String
    """
    endpoint = '/api/clusters/begin_export'
    params = _make_export_params(supplied_clusters, available_clusters, location)
    with InsightiqApi(username=username, password=password) as iiq:
        response = iiq.get(endpoint, params=params)
    return response.json()


def inspect_backup_file(backup_file):
    """Obtain the clusters and size of each backup within the supplied file

    :Returns: String:

    :param backup_file: **Required** The specific InsightIQ backup file to inspect
    :type backup_file: String
    """
    zip_backup = zipfile.ZipFile(backup_file)
    info = {}
    for cluster in zip_backup.infolist():
        if cluster.filename.endswith('.json'):
            continue
        name, _ = os.path.basename(cluster.filename).split('_')
        info[name] = cluster.file_size
    return _format_inspect_output(info)


def _format_inspect_output(info):
    """Create a pretty ASCII table from the backup file contents

    :Returns: String

    :param info: **Required** The mapping of cluster name to backup size
    :type info: Dictionary
    """
    longest_name = len(max(info.keys()))
    biggest_size = len(str(max(info.values())))
    header_string = ' {:^%s} | {:^%s}' % (longest_name, biggest_size)
    row_string = ' {:<%s} | {:>%s}' % (longest_name, biggest_size)

    header = header_string.format('Name', 'Bytes')
    output = [header, '-'] # the - is a placeholder for the seperator
    for name, size in info.items():
        output.append(row_string.format(name, size))

    widest_row = len(max(output, key=len))
    seperator = '-' * widest_row
    output[1] = seperator
    output.append('\n') # so there's a space between the table, and the prompt
    return '\n'.join(output)


def _cleanup_backups(location, max_backups):
    """Automate deletion of oldest backups, so the user doesn't have to.

    :Returns: None

    :param location: The directory used for storing IIQ cluster backups
    :type location: String

    :param max_backups: The maximum number of backups to retain
    :type max_backups: Integer
    """
    if max_backups == 0:
        print('Max backups set to zero, never deleting backups.')
        return
    backups_found = []
    for each_file in os.listdir(location):
        try:
            is_backup_file(os.path.join(location, each_file))
        except argparse.ArgumentTypeError:
            continue
        else:
            backups_found.append(each_file)
    # Might be negative, so floor to zero for better message
    extra_backups = max(len(backups_found) - max_backups, 0)
    print('Found {} extra backups to delete'.format(extra_backups))
    if extra_backups > 0:
        to_delete = []
        # so the oldest is at the start of the list
        backups_found = sorted(backups_found, key=lambda x: int(x.split('_')[2].replace('.zip', '')))
        for idx in range(extra_backups):
            old_backup = backups_found.pop(idx)
            to_delete.append(old_backup)
        for expired_backup in to_delete:
            old_backup_path = os.path.join(location, expired_backup)
            print('Deleting {}'.format(old_backup_path))
            try:
                os.remove(old_backup_path)
            except Exception as doh:
                printerr("Failed to delete backup {}. Error: {}".format(old_backup_path, doh))


def main(cli_args):
    """Entry point function for iiq_cluster_backup script

    :Returns: Integer - The intended exit code for the script

    :param cli_args: **Required** The CLI arguments for the script
    :type cli_args: List
    """
    args = parse_args(cli_args)
    clusters = get_clusters_in_iiq()
    if args.show_clusters:
        clusters_pretty = format_cluster_output(clusters)
        print(clusters_pretty)
        return 0

    if args.inspect:
        print(inspect_backup_file(args.inspect))
        return 0

    if args.all_clusters:
        to_backup = list(get_clusters_in_iiq().keys())
    else:
        to_backup = args.clusters
        if not supplied_clusters_ok(args.clusters, clusters):
            # supplied clusters should be a subset of available clusters
            error = 'Not all supplied clusters available for archiving\n'
            error += 'Available clusters: %s' % clusters.keys()
            error += 'Supplied clusters: %s' % args.clusters
            printerr(error)
            return 2

    # things look good, let's export that data!
    _cleanup_backups(location=args.location, max_backups=args.max_backups)
    try:
        result = export_via_api(to_backup, clusters, args.location, args.username, args.password)
    except ValueError as doh:
        # If the API calls causes IIQ to generate a 4xy or 5xy response, we get HTML
        # instead of JSON. Failure to convert the response to JSON raises ValueError
        return_code = 3
        error = '***Unable to start cluster archive process***\n'
        error += 'Please verify that the insightiq process is running and\n'
        error += 'that the application is functional before attempting to\n'
        error += 'generate another archive backup via this tool.\n\n'
        error += 'If this error persist, please try exporting the cluster(s)\n'
        error += 'via the InsightIQ UI. Additional error information might be\n'
        error += 'found in /var/log/insightiq.log'
        printerr(error)
    except ConnectionError:
        return_code = 4
        error = '***Unable to communicate with the InsightIQ API***\n'
        error += 'Please verify that the insightiq service is running and try again'
        printerr(error)
    else:
        if not result['success']:
            return_code = 5
            printerr(result['msg'])
        else:
            return_code = 0
            msg = 'Cluster archive underway.\nTo monitor status you can either '
            msg += 'follow /var/log/insightiq_export_import.log or\n'
            msg += 'check the Settings page in the InsightIQ UI.'
            print(msg)
    return return_code
