***************
Scripts & Tools
***************

This section goes over the scripts and tools added to your InsightIQ
instance when you install the IIQTools package. Each section should have some
examples of what running the script looks like, or what the tool does.


iiqtools_gather_info
====================

The point of this script is to provide a convenient way for users to collect
logs and configuration information about InsightIQ so that remote support can
investigate any issues that they are having.

Examples (assuming your running as the ``root`` users)
------------------------------------------------------

Printing the *help* message::

  [root@localhost ~]$ iiqtools_gather_info --help
  usage: iiqtools_gather_info [-h] [--output-dir OUTPUT_DIR] --case-number
                       CASE_NUMBER

  Generate a .tar file for debugging InsightIQ

  optional arguments:
    -h, --help            show this help message and exit
    --output-dir OUTPUT_DIR
                          The directory to write the .tgz file to (default:
                          /home/administrator)
    --case-number CASE_NUMBER
                          The Service Request number. Used in naming tar file.
                          (default: None)

Generating a gather::

  [root@localhost ~]$ iiqtools_gather_info --case-number 1234
  2017-09-11 14:53:45,298 - INFO - Collecting config information
  2017-09-11 14:53:46,123 - INFO - Collecting log files
  2017-09-11 14:53:48,126 - INFO - Log gather complete
  2017-09-11 14:53:48,126 - INFO - Created log file /home/administrator/IIQLogs-sr1234-1505166825.tgz


Forgetting to provide the ``--case-number`` argument::

  [root@localhost ~]$ iiqtools_gather_info
  usage: iiqtools_gather_info [-h] [--output-dir OUTPUT_DIR] --case-number
                         CASE_NUMBER
  iiqtools_gather_info: error: argument --case-number is required


Outputting the tar file to a different directory::

  [root@localhost ~]$ iiqtools_gather_info --case-number 1234 --output-dir /datastore
  2017-09-11 14:55:44,195 - INFO - Collecting config information
  2017-09-11 14:55:44,451 - INFO - Collecting log files
  2017-09-11 14:55:45,957 - INFO - Log gather complete
  2017-09-11 14:55:45,957 - INFO - Created log file /datastore/IIQLogs-sr1234-1505166944.tgz


iiqtools_tar_to_zip
===================

Starting with InsightIQ 3.2, you could export a cluster's database from one instance,
then import it later or on another InsightIQ instance. Initially, the exported
data was in `tar file <https://en.wikipedia.org/wiki/Tar_(computing)>`_ format, but in InsightIQ 4.1
we switched to using a `zip file <https://en.wikipedia.org/wiki/Zip_(file_format)>`_. The switch was to
resolve a bug where importing large exports would time out. The data contained
within the tar and the zip files is identical; only the compression format has changed.
This means that if we convert an old tar export to zip, we can use that archive
in newer versions of InsightIQ.

Use cases for this script:

Migration Upgrades
  Instead of upgrading an existing deployment, you export the data on your old
  instance, use this script to convert the format, and then import that data
  on a new deployment of InsightIQ. This approach is ideal for `OVA <https://en.wikipedia.org/wiki/Virtual_appliance>`_
  deployments of InsightIQ because the newer OVAs for InsightIQ have the latest
  security patches applied, and the root partition is configured with `LVM <https://en.wikipedia.org/wiki/Logical_Volume_Manager_(Linux)>`_.

Maintain Legacy Exports
  With the upgrade to 4.1, any datastore exports created on the older version
  of InsightIQ are no longer compatible. This script will update the format
  of those older datastore exports so you can continue to use them in newer
  versions of InsightIQ.


Usage Examples
--------------

Obtaining the *help* message::

  [administrator@localhost ~]$ iiqtools_tar_to_zip --help
  usage: iiqtools_tar_to_zip [-h] -s SOURCE_TAR [-o OUTPUT_DIR]
  Convert .tar to .zip for IIQ datastore export files

  optional arguments:
    -h, --help            show this help message and exit
    -s SOURCE_TAR, --source-tar SOURCE_TAR
                          The source .tar file to convert to .zip (default:
                          None)
    -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                          The (default: /home/administrator)

Simple usage (this export was only about 20MB in size)::

  [administrator@localhost ~]$ iiqtools_tar_to_zip --source-tar /datastore/insightiq_export_1505412864.tar.gz
  2017-09-15 16:57:02,669 - INFO - Converting /datastore/insightiq_export_1505412864.tar.gz to zip format
  2017-09-15 16:57:02,849 - INFO - InsightIQ datastore tar export contained  2 files
  2017-09-15 16:57:02,850 - INFO - Converting insightiq_export_1505412864/dog-pools_003048c644105df4124ad80c701933e83eff.dump
  2017-09-15 16:57:03,120 - INFO - Converting insightiq_export_1505412864/dog-pools_003048c644105df4124ad80c701933e83eff_config.json
  2017-09-15 16:57:03,160 - INFO - New zip formatted file saved to /home/administrator/insightiq_export_1505412864.zip

Creating the new zip in a different directory::

  [administrator@localhost ~]$ iiqtools_tar_to_zip --source-tar /datastore/insightiq_export_1505412864.tar.gz --output-dir /tmp
  2017-09-15 17:00:08,897 - INFO - Converting /datastore/insightiq_export_1505412864.tar.gz to zip format
  2017-09-15 17:00:09,073 - INFO - InsightIQ datastore tar export contained  2 files
  2017-09-15 17:00:09,073 - INFO - Converting insightiq_export_1505412864/dog-pools_003048c644105df4124ad80c701933e83eff.dump
  2017-09-15 17:00:09,337 - INFO - Converting insightiq_export_1505412864/dog-pools_003048c644105df4124ad80c701933e83eff_config.json
  2017-09-15 17:00:09,374 - INFO - New zip formatted file saved to /tmp/insightiq_export_1505412864.zip


iiqtools_version
================

A rather straght forward script that prints the version of InsightIQ
and IIQTools that's installed.

Example Usage::

  [administrator@localhost ~]$ iiqtools_version
  InsightIQ: 4.1.1.3
  IIQTools: 0.1.0


iiqtools_patch
==============

A tool for installing, uninstalling, and displaying patches to IsightIQ source code.

.. note::

   Installing **and** uninstalling requires the InsightIQ application to be restarted.
   Running the ``iiqtools_patch`` tool with ``sudo`` will automatically restart the application.

Display all installed patches::

  [administrator@localhost ~]$ iiqtools_patch --show

          Patches
          -------
          patch1234

          Count: 1

Display details for a specific patch::

  [administrator@localhost ~]$ iiqtools_patch --show

  Here's an example patch details


Uninstalling a patch as a non-root user::

  [administrator@localhost ~]$ iiqtools_patch --uninstall patch1234
  2017-10-03 12:49:19,656 - INFO - Successfully uninstalled patch
  2017-10-03 12:49:19,657 - INFO - Non-root user detected for patch install. Unable to restart InsightIQ.
  2017-10-03 12:49:19,657 - INFO - **Patch wont take effect unless you restart InsightIQ**

  2017-10-03 12:49:19,657 - INFO - Please run the following command to restart InsightIQ:
  2017-10-03 12:49:19,657 - INFO - sudo service insightiq restart


Installing a patch with ``sudo``::

  [administrator@localhost ~]$ sudo iiqtools_patch --install insightiq-patch-1234.tgz
  [sudo] password for administrator:
  2017-10-03 12:54:26,643 - INFO - Installed IIQ version: 4.1.1.3
  2017-10-03 12:54:26,644 - INFO - Patch min version: 4.1.0
  2017-10-03 12:54:26,644 - INFO - Patch max version: 4.1.1.3
  2017-10-03 12:54:26,645 - INFO - Successfully installed patch
  2017-10-03 12:54:26,645 - INFO - Restarting InsightIQ
  2017-10-03 12:54:34,098 - INFO - Stopping insightiq:       [  OK  ]
  Starting insightiq:                                        [  OK  ]


iiqtools_cluster_backup
=======================

The point of this tool is to make automating backups of your cluster data easy;
just setup a `crontab <https://opensource.com/article/17/11/how-use-cron-linux>`_!

InsightIQ supports exporting/importing cluster data, but it requires a user to
click through the UI. This tool calls the same API as the UI, but instead does
the API call from the CLI instead of a browser. The API that is called requires
a user with elevated privileges for the backup to work. Attempting to use a
read-only user will cause your backups to fail. To be clear, this tool needs an
admin of InsightIQ, not the host Linux machine running the InsightIQ application.

.. note::
  It's highly recommend to setup a local user instead of using the default ``administrator``.


Setting up the ``iiq_backup`` user account
------------------------------------------

The default ``administrator`` account used by InsightIQ has ``sudo`` power over the host
machine running the application. In other words, that account is root by a different name.
The iiqtools_cluster_backup tool requires a password to be supplied, either as a CLI argument
or interactively. When setting up a crontab, you must use the CLI argument option.
This means that the password will be in clear text in the crontab file. **TODO link to stackoverflow** This is the
main reason that setting up an alternate account is a great idea! All local users
on the host machine running InsightIQ are by default admin account in the application.

To create the ``iiq_backup`` user account, run the following command::

  [administrator@localhost ~]$ sudo useradd iiq_backup && sudo passwd iiq_backup

Once that user is created, you'll have to give them access to the key file::

  [administrator@localhost ~]$ sudo chmod 440 /etc/isilon/secret_key
  [administrator@localhost ~]$ sudo chown :iiq_backup /etc/isilon/secret_key


Usage Examples
--------------

Here are some examples of using the iiqtools_backup_cluster tool.

Printing available clusters::

  [administrator@localhost ~]$ iiqtools_cluster_backup --show-clusters
  Clusters monitored by InsightIQ
  -------------------------------
    myCluster
    myOtherCluster
    isi-nas-01

Interactively supplying the password::

  [administrator@localhost ~]$ iiqtools_cluster_backup --clusters myOtherCluster --location /mnt/backups --username iiq_backup
  Please enter the password for iiq_backup :
  Cluster archive underway.
  To monitor status you can either follow /var/log/insightiq_export_import.log or
  check the Settings page in the InsightIQ UI.

Backing up to an NFS export::

  [administrator@localhost ~]$ iiqtools_cluster_backup --clusters myCluster --location 10.7.1.2:/ifs/data --username iiq_backup --password a
  Cluster archive underway.
  To monitor status you can either follow /var/log/insightiq_export_import.log or
  check the Settings page in the InsightIQ UI.

Backing up multiple clusters::

  [administrator@localhost ~]$ iiqtools_cluster_backup --clusters myCluster isi-nas-01 --location /mnt/backups --username iiq_backup --password a
  Cluster archive underway.
  To monitor status you can either follow /var/log/insightiq_export_import.log or
  check the Settings page in the InsightIQ UI.

Trying to backup a cluster while the InsightIQ application is offline::

  [administrator@localhost ~]$ iiqtools_cluster_backup --clusters myCluster --location 10.7.1.2:/ifs/data --username iiq_backup --password a
  ***Unable to communicate with the InsightIQ API***
  Please verify that the insightiq service is running and try again


Crontab Examples
----------------

This section assumes you've created the ``iiq_backup`` user account.

.. note::

  Only one backup can happen at a time.

Backup every Monday at 1:00 AM ::

  0 1 * * * mon iiqtools_cluster_backup --clusters myCluster myOtherCluster isi-nas-01 --location isi-nas.corp:/ifs/iiq/backups --username iiq_backup --password a

Backup only the cluster you care about, once a month at 2:00 AM ::

  0 2 1 * * * iiqtools_cluster_backup --clusters myCluster --location /mnt/backups --username iiq_backup --password a
