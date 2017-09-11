***************
Scripts & Tools
***************

This section goes over the scripts and tools added to your InsightIQ
instance when you install the IIQTools package. Each section should have some
examples of what running the script looks like, or what the tool does.


iiq_gather_info
===============

The point of this script is to provide a convenient way for users to collect
logs and configuration information about InsightIQ so that remote support can
investigate any issues that they are having.

Examples (assuming your running as the ``root`` users)
------------------------------------------------------

Printing the *help* message::

  [root@localhost ~]$ iiq_gather_info --help
  usage: iiq_gather_info [-h] [--output-dir OUTPUT_DIR] --case-number
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

  [root@localhost ~]$ iiq_gather_info --case-number 1234
  2017-09-11 14:53:45,298 - INFO - Collecting config information
  2017-09-11 14:53:46,123 - INFO - Collecting log files
  2017-09-11 14:53:48,126 - INFO - Log gather complete
  2017-09-11 14:53:48,126 - INFO - Created log file /home/administrator/IIQLogs-sr1234-1505166825.tgz


Forgetting to provide the ``--case-number`` argument::

  [root@localhost ~]$ iiq_gather_info
  usage: iiq_gather_info [-h] [--output-dir OUTPUT_DIR] --case-number
                         CASE_NUMBER
  iiq_gather_info: error: argument --case-number is required


Outputting the tar file to a different directory::

  [root@localhost ~]$ iiq_gather_info --case-number 1234 --output-dir /datastore
  2017-09-11 14:55:44,195 - INFO - Collecting config information
  2017-09-11 14:55:44,451 - INFO - Collecting log files
  2017-09-11 14:55:45,957 - INFO - Log gather complete
  2017-09-11 14:55:45,957 - INFO - Created log file /datastore/IIQLogs-sr1234-1505166944.tgz
