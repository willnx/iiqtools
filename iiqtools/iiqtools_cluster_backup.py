# -*- coding: UTF-8 -*-
"""
This module contains all the business logic for creating an archive backup
of OneFS cluster data within InsightIQ.
"""
from __future__ import print_function
import json
import getpass
import argparse

import requests
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
from iiqtools.utils.insightiq_api import InsightiqApi, Parameters


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

    parser.add_argument('-l', '--location',
        help='The NFS mount or local file system location to save the archive file to')
    parser.add_argument('-u', '--username',
        help='The Administrative user to authenticate as')
    parser.add_argument('-p', '--password',
        help="The Administrative user's password. If not supplied, you will be "
              "prompted for it; this avoids leaving the password in your shell history")

    args = parser.parse_args(cli_args)
    if args.clusters:
        if not (args.location and args.username):
            parser.error('-l/--location required when supplying -c/--clusters')
        if not args.password:
            args.password = getpass.getpass('Password for %s :' % args.username)
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
        result = response.json()
    return result


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

    if not supplied_clusters_ok(args.clusters, clusters):
        # supplied clusters should be a subset of available clusters
        error = 'Not all supplied clusters available for archiving\n'
        error += 'Available clusters: %s' % clusters.keys()
        error += 'Supplied clusters: %s' % args.clusters
        printerr(error)
        return 2

    # things look good, let's export that data!
    try:
        result = export_via_api(args.clusters, clusters, args.location, args.username, args.password)
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
    else:
        if not result['success']:
            return_code = 4
            printerr(result['msg'])
        else:
            return_code = 0
            msg = 'Cluster archive underway.\nTo monitor status you can either '
            msg += 'follow /var/log/insightiq_export_import.log or\n'
            msg += 'check the Settings page in the InsightIQ UI.'
            print(msg)
    return return_code
