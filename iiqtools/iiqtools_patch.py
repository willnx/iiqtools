# -*- coding: UTF-8 -*-
"""
This module contains all the business logic for patching InsightIQ.
"""
from __future__ import print_function

import os
import sys
import glob
import shutil
import tarfile
import hashlib
import getpass
import argparse
from StringIO import StringIO
from collections import namedtuple

from configobj import ConfigObj

from iiqtools.utils import shell, versions
from iiqtools.utils.logger import get_logger


#########################################
# Data structures and related functions #
#########################################


_PatchContents = namedtuple("PatchContents", "readme meta_ini patched_files")
# So we can have a nice docstring for the namedtuple
class PatchContents(_PatchContents):
    """The extracted data from a patch file

    :param readme: The contents of the README.txt file
    :type readme: String

    :param meta_ini: The contents of the meta.ini file
    :type meta_ini: String

    :param patched_files: A mapping of patched files to the updated content
    :type patched_files: Dictionary
    """
    pass


def extract_patch_contents(patch_path, log):
    """Convert the contents of a patch file into a usable data structure

    Yes, while this does read the whole patch into memory, it's highly unlikely
    that a patch for InsightIQ will be more than a dozen MB in size. By reading
    the patch into memory and generating a data structure for it, we exponentially
    increase out ability to unit test the patching logic.

    :Returns: TarContents (namedtuple)

    :param patch_path: **Required** The file system location of the patch file
    :type patch_path: String

    :param log: **Required** The logging object
    :type log: logging.Logger
    """
    log.debug("Validating patch at %s", patch_path)

    the_tar = tarfile.open(patch_path)
    tar_contents = the_tar.getmembers()
    meta_ini = None
    readme = None
    patched_files = {}
    for item in tar_contents:
        log.debug('Checking %s', item.path)
        if item.isdir():
            log.debug('Ignoring intermediate subdirectory')
            continue
        elif os.path.basename(item.path) == 'meta.ini':
            meta_ini = the_tar.extractfile(item.path).read()
            log.debug('Patch meta.ini contents:\n %s', meta_ini)
        elif os.path.basename(item.path) == 'README.txt':
            readme = the_tar.extractfile(item.path).read()
            log.debug('Patch README.txt found')
        else:
            patched_files[item.path] = the_tar.extractfile(item.path).read()
            log.debug('Added source file %s', item.path)
    the_tar.close()
    return PatchContents(readme, meta_ini, patched_files)


################################################
# Validators - Ensure and enforce requirements #
################################################

def check_file(cli_value):
    """Validate that the supplied value is actually a tar file that can be read

    This function is intended to be used with the argparse lib as an
    `argument type <https://docs.python.org/2.7/library/argparse.html#type>`_.

    :Raises: argparse.ArgumentTypeError

    :Returns: String

    :param cli_value: **Required** The value supplied by the end user
    :type cli_value: String
    """
    try:
        if not tarfile.is_tarfile(cli_value):
            msg = 'Supplied value is not a tar file: %s' % cli_value
            raise argparse.ArgumentTypeError(msg)
    except IOError as doh:
        # doesn't exist, or we can't read it
        msg = '%s: %s' % (doh.strerror, doh.filename)
        raise argparse.ArgumentTypeError(msg)
    else:
        return cli_value


def parse_cli(the_cli_args):
    """Defines the CLI for iiq_patch

    :Returns: argparse.Namespace

    :param the_cli_args: **Required** The commands from the CLI
    :type the_cli_args: List
    """
    parser = argparse.ArgumentParser(description='For installing/removing patches to InsightIQ',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    mutually_exclusive = parser.add_mutually_exclusive_group(required=True)
    mutually_exclusive.add_argument('-s', '--show', const='', nargs='?',
        help='Display patches that are installed. Supply value for info about that patch.')
    mutually_exclusive.add_argument('-i', '--install', type=check_file,
        help='The patch file you want to install')
    mutually_exclusive.add_argument('-u', '--uninstall',
        help='The name of the patch to remove')

    parser.add_argument('-d', '--debug', action='store_true',
        help='Increase the log level for iiq_patch')

    args = parser.parse_args(the_cli_args)
    return args


def patch_is_valid(contents, log):
    """Verify that the supplied patch file contents are OK

    :Returns: Boolean

    :param contents: **Required** The extracted patch file data
    :type contents: PatchContents

    :param log: **Required** The logging object
    :type log: logging.Logger
    """
    # Validate patch contained all expected data
    if not (contents.readme and contents.meta_ini and contents.patched_files):
        log.debug("patch is missing required data")
        return False

    # Validate the meta.ini contents
    config = ConfigObj(StringIO(contents.meta_ini))
    config_headers = set(config.keys())
    log.debug("meta.ini headers: %s", config_headers)
    if not config_headers == set(['info', 'version', 'files']):
        return False

    config_info_fields = set(config['info'].keys())
    log.debug("meta.ini info fields: %s", config_info_fields)
    if not config_info_fields == set(['name', 'bug']):
        return False

    config_version_fields = set(config['version'].keys())
    log.debug("meta.ini version fields: %s", config_version_fields)
    if not config_version_fields == set(['minimum', 'maximum']):
        return False

    if not len(config['files'].keys()) >= 1:
        log.debug('Supplied patch does not define what files to patch')
        return False
    for file_path in config['files'].keys():
        if file_path.startswith('/'):
            log.debug('Invalid file location for %s', file_path)
            return False
    return True


def source_is_patchable(files_to_patch, iiq_dir, log):
    """Compare the md5 hashes supplied in the patch with the md5 hashes of the
    currently installed source files.

    This function enables us to avoid installing a new patch that clobbers and
    existing patch; i.e. patch-b overwrites a file patched by patch-a.

    :Returns: Boolean

    :param files_to_patch: **Required** The mapping of file location to expected md5 hash of the source
    :type files_to_patch: Dictionary

    :param iiq_dir: **Required** The file system path where InsightIQ source is located.
    :type iiq_dir: String

    :param log: **Required** The logging object
    :type log: logging.Logger
    """
    is_patchable = True
    for the_file, the_hash in files_to_patch.items():
        abs_location = join_path(iiq_dir, the_file)
        log.debug('Checking IIQ source file %s', abs_location)
        log.debug("Expected hash %s for %s", the_hash, abs_location)
        try:
            md5_ok = md5_matches(abs_location, the_hash, log)
        except (IOError, OSError) as doh:
            log.error(doh)
            is_patchable = False
            break
        else:
            if not md5_ok:
                is_patchable = False
                break
            else:
                log.debug("Hashes match for %s", abs_location)
    return is_patchable


def version_ok(version_info, log):
    """Ensure the patch applies to the installed version of InsightIQ

    :Returns: Boolean

    :param version_info: **Required** Contains the minimum and maximum versions
                         of InsightIQ that the patch applies to.
    :type version_info: Dictionary

    :param log: **Required** The logging object
    :type log: logging.Logger
    """
    iiq_version = versions.get_iiq_version()
    min_version = versions.Version(name='patch-min', version=version_info['minimum'])
    max_version = versions.Version(name='patch-max', version=version_info['maximum'])
    log.info('Installed IIQ version: %s', iiq_version.version)
    log.info('Patch min version: %s', min_version.version)
    log.info('Patch max version: %s', max_version.version)
    return min_version <= iiq_version <= max_version


def md5_matches(file_location, md5_hash, log):
    """Determines if a supplied md5 hex matches the md5 for a given file

    :Returns: Boolean

    :param file_location: The file system path of the file to check
    :type file_location: String

    :param md5_hash: The expected md5 hash for the file, in hexadecimal format
    :type md5_hash: String

    :param log: **Required** The logging object
    :type log: logging.Logger
    """
    with open(file_location) as the_file:
        data = the_file.read()
    hasher = hashlib.md5()
    hasher.update(data)
    file_hash = hasher.hexdigest()
    log.debug('Found hash %s for %s', file_hash, file_location)
    return md5_hash == file_hash


def expected_backups(found_backups, expected_backups, log):
    """Verify the names and count of backed-up source files matches the original meta.ini

    :Returns: Boolean

    :param found_backups: **Required** The contents of the patch directory (i.e. listdir)
    :type found_backups: List

    :param expected_backups: **Required** The list of files that were patched (based of meta.ini)
    :type expected_backups: List

    :param log: **Required** The logging object
    :type log: logging.Logger
    """
    backup_files = set(found_backups)
    expected = set([convert_patch_name(x, to='backup') for x in expected_backups])
    log.debug("Found backups: %s", backup_files)
    log.debug("Expected backups: %s", expected_backups)
    if backup_files > expected:
        log.error("Found unexpected copies of original source files")
        return False
    elif backup_files < expected:
        log.error("Missing backups of original source files")
        return False
    elif backup_files != expected:
        log.error("Mismatching files between backups and expected backups")
        return False
    elif len(backup_files) != len(found_backups):
        log.error("Duplicate copies of backups found")
        return False
    else:
        return True


###################################################################
# Utility functions - Centralize conventions to avoid duplication #
###################################################################

def convert_patch_name(name, to='source'):
    """Coverts between the directory naming pattern, and the backup name.

    The patch installation creates backups of the source files. To avoid re-creating
    the directory structure of the source for the backup, we replace the forward
    slash ``/`` with a double-underbar ``__``. The double-underbar prevents us from
    accidentally converting ``my_module.py`` to ``my/module.py``

    Convert source file to backup name::

        >>> convert_patch_name('insightiq/controllers/security.py', to='backup')
        >>> 'insightiq__controllers__security.py'

    Convert backup to source name::

        >>> convert_patch_name('insightiq__controllers__security.py', to='source')
        >>> 'insightiq/controllers/security.py'

    :Returns: String

    :Raises: ValueError

    :param name: **Required** The name to convert
    :type name: String

    :param to: The target naming pattern
    :type to: Enum -> 'source', 'backup'
    """
    if to == 'source':
        return name.replace('___', '/')
    elif to == 'backup':
        return name.replace('/', '___')
    else:
        raise ValueError('param "to" must be either "source" or "backup", supplied: %s' % to)


def patch_backups_path(patch_dir):
    """Ceneralizes how other functions can reference the backups of original source files

    :Returns: String

    :param patch_dir: **Required** The file system path to the specific patch directory
    :type patch_dir: String
    """
    return '%s/originals' % patch_dir


def join_path(*args):
    """Join an arbitrary number of strings as a Linux/Unix file path

    Used in place of ``os.path.join`` so tests can run on Windows or Linux
    without generating false positives.

    Example::
        >>> join_path('some', 'directory')
        some/directory
        >>> join_path('/home', )

    :Returns: String

    :params args: **Required** The strings to join together
    :type args: String
    """
    return '/'.join(args)


#########################################################################
# Command handlers - carries out the procedure for the specific command #
#########################################################################

def restore_originals(iiq_dir, patch_dir, backup_files):
    """Replaces the patched source files with the backed up copies

    :Returns: None

    :param iiq_dir: The file system path to the InsightIQ source code
    :type iiq_dir: String

    :param patch_dir: The file system path to the patches directory
    :type patch_dir: String

    :param backup_files: The list of valid copies of the original source files
    :type backup_files: List
    """
    backups_dir = patch_backups_path(patch_dir)
    for backup in backup_files:
        source_name = convert_patch_name(backup, to='source')
        source_path = join_path(iiq_dir, source_name)
        backup_path = join_path(backups_dir, backup)
        source_pyc = source_path + 'c'
        shutil.copyfile(backup_path, source_path)
        if os.path.isfile(source_pyc):
            os.remove(source_pyc)


def install_patch(patch_content, patch_info, patch_name, log):
    """Does the actual installation of the InsightIQ patch

    :Returns: None

    :param patch_content: **Required** The extracted data from the patch file.
    :type patch_content: PatchContent (namedtuple)

    :param patch_info: **Required** The current state of patches installed.
    :type patch_info: PatchInfo (namedtuple)

    :param patch_name: **Required** The human reference to this patch.
    :type patch_name: String

    :param log: **Required** The logging object
    :type log: logging.Logger
    """
    patch_dir = join_path(patch_info.patches_dir, patch_name)
    patch_dir_backups = patch_backups_path(patch_dir)
    os.mkdir(patch_dir)
    os.mkdir(patch_dir_backups)
    # back up all source files 1st
    for file_location in patch_content.patched_files.keys():
        # no need to re-recreate directory structure under the patch dir for the backup
        backup_name = convert_patch_name(file_location, to='backup')
        backup_copy = join_path(patch_dir_backups, backup_name)
        original_copy = join_path(patch_info.iiq_dir, file_location)
        shutil.copyfile(original_copy, backup_copy)

    # Add README.txt to patch directory
    readme_location = join_path(patch_dir, 'README.txt')
    log.debug('Writing readme to %s', readme_location)
    with open(readme_location, 'w') as readme_file:
        readme_file.write(patch_content.readme)

    # Add meta.ini to patch directory
    meta_location = join_path(patch_dir, 'meta.ini')
    log.debug("Writing meta.ini to %s", meta_location)
    with open(meta_location, 'w') as meta_file:
        meta_file.write(patch_content.meta_ini)

    # Overwrite original source with patched version
    for patched_file, patched_data in patch_content.patched_files.items():
        location = join_path(patch_info.iiq_dir, patched_file)
        with open(location, 'w') as the_file:
            the_file.write(patched_data)
        # Delete any .pyc files
        if location.endswith('.py'):
            pyc = location + 'c'
            if os.path.isfile(pyc):
                os.remove(pyc)


def handle_show(specific_patch, log):
    """Implements the ``--show`` logic for iiq_patch.

    This function must be able to either display all installed patches, or
    details for a specific patch. The return value from the function must be
    the expected exit code for the iiq_patch script (i.e. non-zero for errors).

    :Returns: Integer

    :param specific_patch: **Required** The name of a specific patch to obtain
                           details for. Supply an zero length string to print
                           all installed patches to the console.
    :type specific_patch: String

    :param log: **Required** The logging object
    :type log: logging.Logger
    """
    exit_code = 0
    patch_info = versions.get_patch_info(specific_patch, log)
    log.debug(patch_info)
    if not patch_info.all_patches:
        log.info('No patches installed')

    elif specific_patch:
        log.debug('Looking up info for patch %s', specific_patch)
        if not patch_info.is_installed:
            log.error('Supplied patch does not exist: %s', patch_info.specific_patch)
            exit_code = 50
        elif not patch_info.readme:
            log.error('Unable to find patch details for %s', patch_info.specific_patch)
            exit_code = 51
        else:
            log.info('Details for patch %s\n', patch_info.specific_patch)
            print(patch_info.readme, '\n')
    else:
        # just wants a list of all patches
        log.debug("All patches: %s", patch_info.all_patches)
        msg = '\n\tPatches\n\t-------'
        msg += '\n\t%s\n' % '\n\t'.join(patch_info.all_patches)
        msg += '\n\tCount: %s\n' % len(patch_info.all_patches)
        print(msg)

    return exit_code


def handle_install(patch_path, log):
    """Entry point for installing a patch in InsightIQ.

    The returned integer is the intended exit code for the iiq_patch script.
    All explicitly defined exit codes (i.e. ones we don't bubble up from the system)
    must start at 100, and cannot exceed 199.

    :Returns: Integer

    :param patch_path: The file system location of the patch file
    :type patch_path: String

    :param log: The logging object
    :type log: logging.Logger
    """
    patch_info = versions.get_patch_info(specific_patch='', log=log)
    if not patch_info.iiq_dir:
        # IIQ is not installed, no way to install patch
        return 100

    # Prep system for patch installation
    try:
        os.mkdir(patch_info.patches_dir)
    except (OSError, IOError) as doh:
        if doh.errno == 13:
            log.error('Unable to setup patching directory')
            log.error("Please re-run with root privileges")
            return doh.errno
        elif doh.errno == 17:
            # dir already exists; likely already has a patch installed
            pass
        else:
            log.error(doh)
            if log.level == 10:
                log.exeception(doh)
            return doh.errno

    # Argprase should already have verified we can read the patch file
    # so no need to try/except for IO/OS errors
    patch_content = extract_patch_contents(patch_path, log)
    if not patch_is_valid(patch_content, log):
        log.error('Malformed patch file supplied')
        return 101
    meta_config = ConfigObj(StringIO(patch_content.meta_ini))
    if meta_config['info']['name'] in patch_info.all_patches:
        log.info('Patch %s is already installed', meta_config['info']['name'])
        return 0
    if not version_ok(meta_config['version'], log):
        log.error('Supplied patch does not apply to current version of InsightIQ')
        return 102
    if not source_is_patchable(meta_config['files'], patch_info.iiq_dir, log):
        log.error("Unable to install patch. Please contact Isilon support.")
        return 103
    try:
        install_patch(patch_content=patch_content,
                      patch_info=patch_info,
                      patch_name=meta_config['info']['name'],
                      log=log)
    except (IOError, OSError) as doh:
        specific_patch_dir = join_path(patch_info.patches_dir, meta_config['info']['name'])
        # ignore_errors encase the patch specific dir was never made
        shutil.rmtree(specific_patch_dir, ignore_errors=True)
        log.error(doh)
        log.info('Unable to install patch')
        if log.level == 10:
            # i.e. debug logging
            log.exception(doh)
        return 104
    else:
        log.info('Successfully installed patch')
    return 0


def handle_uninstall(patch_name, log):
    """Carries out the task of uninstalling a patch

    The returned integer is the exit code for the script. All explicitly defined
    exit codes (i.e. ones we don't bubble up from the system) must start at
    200, and cannot exceed 255.

    :Returns: Integer

    :param patch_name: **Required** The name of the patch to uninstall
    :type patch_name: String

    :param log: **Required** The logging object.
    :type log: logging.Logger
    """
    patch_info = versions.get_patch_info(specific_patch=patch_name, log=log)
    patch_dir = join_path(patch_info.patches_dir, patch_name)
    if not patch_info.is_installed:
        log.info('Patch %s is not installed', patch_name)
        return 200

    meta_location = join_path(patch_dir, 'meta.ini')
    try:
        meta_config = ConfigObj(meta_location)
    except (IOError, OSError) as doh:
        log.error(doh)
        log.info('Unable to uninstall patch %s', patch_name)
        return 201

    backups_dir = patch_backups_path(patch_dir)
    backup_files = os.listdir(backups_dir)
    if not expected_backups(backup_files, meta_config['files'].keys(), log):
        log.error("Unable to remove patch")
        return 202

    for original_path, original_hash in meta_config['files'].items():
        backup_name = convert_patch_name(original_path, to='backup')
        backup_file = join_path(backups_dir, backup_name)
        if not md5_matches(backup_file, original_hash, log):
            return 203

    try:
        restore_originals(patch_info.iiq_dir, patch_dir, backup_files)
    except (IOError, OSError) as doh:
        log.error("Unable to complete restore of original source files")
        log.error(doh)
        return doh.errno

    try:
        shutil.rmtree(patch_dir)
    except (IOError, OSError) as doh:
        log.error("Unable to dereference patch: %s", patch_name)
        log.error(doh)
        log.error('Please manually delete: %s', patch_dir)
        return doh.errno
    else:
        log.info("Successfully uninstalled patch")
    return 0


def main(the_cli_args):
    """Entry point function for iiq_patch"""
    args = parse_cli(the_cli_args)
    if args.debug:
        log_level = 10
    else:
        log_level = 20
    log = get_logger(log_path='/dev/null', stream_lvl=log_level, file_lvl=log_level)

    if args.install:
        exit_code = handle_install(args.install, log)
    elif args.uninstall:
        exit_code = handle_uninstall(args.uninstall, log)
    else:
        exit_code = handle_show(args.show, log)
    log.debug('Exit code: %s', exit_code)
    if (not exit_code) and (args.install or args.uninstall):
        # successfully installed or uninstalled the patch
        restart_syntax = 'service insightiq restart'
        if getpass.getuser() == 'root':
            log.info('Restarting InsightIQ')
            result = shell.run_cmd(restart_syntax)
            log.info(result.stdout)
            log.debug('Sterr from retart syntax: %s', result.stderr)
            log.debug('Restart syntax: %s', result.command)
            log.debug('Restart exitcode: %s', result.exit_code)
        else:
            log.info('Non-root user detected for patch install. Unable to restart InsightIQ.')
            log.info('**Patch wont take effect unless you restart InsightIQ**\n')
            log.info('Please run the following command to restart InsightIQ:')
            log.info('sudo %s', restart_syntax)
    return exit_code
