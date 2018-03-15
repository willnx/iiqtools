# -*- coding: UTF-8 -*-
"""
This script converts the format of datastore exports (not the CSV exports) from
tar to zip. In InsightIQ 4.1, the format was changed to fix bug 162840, in which
an attempt to import a large datastore export would time out. The only change
to the exported data is the format. So to use an export from an older instance
(before 4.1) all you have to convert the format. In other words, the data is still
the same, it's just a different compression format in InsightIQ 4.1.
"""
import os
import re
import zlib
import struct
import tarfile
import zipfile
import argparse
import binascii

from iiqtools.utils.logger import get_logger
from iiqtools.utils.generic import check_path


class BufferedZipFile(zipfile.ZipFile):
    """A subclass of zipfile.ZipFile that can read from a file-like object and
    stream the contents into a new zip file.
    """

    def writebuffered(self, filename, file_handle):
        """Stream write data to the zip archive

        :param filename: **Required** The name to give the data once added to the zip file
        :type filename: String

        :param file_handle: **Required** The file-like object to read
        :type file_handle: Anything that supports the `read <https://docs.python.org/2/tutorial/inputoutput.html#methods-of-file-objects>`_ method
        """
        zinfo = zipfile.ZipInfo(filename=filename)

        zinfo.file_size = file_size = 0
        zinfo.flag_bits = 0x00
        zinfo.header_offset = self.fp.tell()

        self._writecheck(zinfo)
        self._didModify = True

        zinfo.CRC = CRC = 0
        zinfo.compress_size = compress_size = 0
        self.fp.write(zinfo.FileHeader())
        if zinfo.compress_type == zipfile.ZIP_DEFLATED:
            cmpr = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
        else:
            cmpr = None

        while True:
            buf = file_handle.read(1024 * 8)
            if not buf:
                break

            file_size = file_size + len(buf)
            CRC = binascii.crc32(buf, CRC) & 0xffffffff
            if cmpr:
                buf = cmpr.compress(buf)
                compress_size = compress_size + len(buf)

            self.fp.write(buf)

        if cmpr:
            buf = cmpr.flush()
            compress_size = compress_size + len(buf)
            self.fp.write(buf)
            zinfo.compress_size = compress_size
        else:
            zinfo.compress_size = file_size

        zinfo.CRC = CRC
        zinfo.file_size = file_size

        position = self.fp.tell()
        self.fp.seek(zinfo.header_offset + 14, 0)
        self.fp.write(struct.pack("<LLL", zinfo.CRC, zinfo.compress_size, zinfo.file_size))
        self.fp.seek(position, 0)
        self.filelist.append(zinfo)
        self.NameToInfo[zinfo.filename] = zinfo


def check_tar(value):
    """Validate that the supplied tar file is an InsightIQ datastore export file.

    :Raises: argparse.ArgumentTypeError

    :Returns: String

    :param value: **Required** The CLI value to validate
    :type value: String
    """
    regex = re.compile("^insightiq_export_\d{10}.tar.gz$")
    try:
        if not os.path.isfile(value):
            msg = 'value %s does not exist' % value
            raise argparse.ArgumentTypeError(msg)
        elif not tarfile.is_tarfile(value):
            msg = 'value %s is not a tar file'
            raise argparse.ArgumentTypeError(msg)
        elif not regex.search(os.path.basename(value)):
            msg = 'value is not a valid InsightIQ datastore export file'
            raise argparse.ArgumentTypeError(msg)
    except IOError as doh:
        # IOError is generated if we cannot read the tar file; i.e. lack permissions
        raise argparse.ArgumentTypeError(doh)
    else:
        return value


def parse_cli(the_cli_args):
    """Handles parsing the CLI, and gives us --help for (basically) free

    :Returns: argparse.Namespace

    :param cli_args: **Required** The arguments passed to the script
    :type cli_args: List
    """
    parser = argparse.ArgumentParser(description='Convert .tar to .zip for IIQ datastore export files',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-s', '--source-tar', type=check_tar, required=True,
        help='The source .tar file to convert to .zip')
    parser.add_argument('-o', '--output-dir', type=check_path, default='/home/administrator',
        help='The ')

    args = parser.parse_args(the_cli_args)
    return args


def get_timestamp_from_export(source_tar):
    """Allows us to create the new zip archive with the correct timestamp

    :Returns: String

    :param source_tar: **Required** The tar that's being converted to a zip
    :type source_tar: String
    """
    # In case source_tar is provided as a file path
    source_file = os.path.basename(source_tar)
    # file name convention is insightiq_export_TIMESTAMP.tar.gz
    insightiq = 0
    export = 1
    timestamp = 2
    return source_file.rstrip('.tar.gz').split('_')[timestamp]


def joinname(export_dir, file_name):
    """The tar/zip used by InsightIQ expects the data nested in a directory.
    This function handles absolute and relative paths for file_name.

    :Returns: String

    :param export_dir: **Required** The directory name to nest the file under
    :type export_dir: String

    :param file_name: **Required** The name of the filed nested in the directory
    :type file_name: String
    """
    name = os.path.basename(file_name)
    return '%s/%s' % (export_dir, name)


def main(the_cli_args):
    """Entry point for the iiq_tar_to_zip script"""
    args = parse_cli(the_cli_args)
    log = get_logger(log_path='/dev/null', stream_lvl=10, file_lvl=10)

    log.info('Converting %s to zip format', args.source_tar)
    original_timestamp = get_timestamp_from_export(args.source_tar)
    zip_export_dir = "insightiq_export_%s" % original_timestamp
    zip_export_name = zip_export_dir + '.zip'
    zip_export_path = os.path.join(args.output_dir, zip_export_name)

    try:
        zip_export = BufferedZipFile(zip_export_path, mode='w', allowZip64=True)
    except IOError as doh:
        log.error('Unable to create zip file: %s', doh)
        return 1

    tar_export = tarfile.open(args.source_tar)
    tar_files = tar_export.getmembers()
    log.info('InsightIQ datastore tar export contained %s files', len(tar_files))
    for the_file in tar_files:
        file_handle = tar_export.extractfile(the_file)
        log.info('Converting %s', the_file.name)
        try:
            filename = joinname(zip_export_dir, the_file.name)
            zip_export.writebuffered(filename=filename, file_handle=file_handle)
        except (IOError, OSError) as doh:
            log.error(doh)
            log.error('Deleting zip file')
            os.remove(zip_export_path)
            return doh.errno

    zip_export.close()
    tar_export.close()
    log.info('New zip formatted file saved to %s', zip_export_path)
    return 0
