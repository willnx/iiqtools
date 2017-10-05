******************
Patching InsightIQ
******************

This section explains how the patching mechanism works and how to create new
patches for InsightIQ. This section is indented for source code contributors.

If you're looking for documentation about install/uninstall patches, please
checkout the `Scripts <https://iiqtools.readthedocs.io/en/latest/scripts.html>`_ section.


How patching works
==================

Where patches are stored
------------------------

The patching mechanism creates a directory under the installation path of the
InsightIQ source code. For example, if you deploy a new `OVA <https://en.wikipedia.org/wiki/Virtual_appliance>`_
of InsightIQ 4.1.1, the installation path is
``/usr/share/isilon/lib/python2.7/site-packages/insightiq``. The directory created
is named ``patches``, for obvious reasons. The ``patches`` directory contains subdirectories;
one for each patch currently installed.

The reason for putting the ``patches`` directory under the InsightIQ source code
is it simplifies upgrades. When you ask the patching mechanism "what patches are
currently installed" after an upgrade, it'll always report that no patches are
installed. In otherwords, upgrading InsightIQ removes all patches. There's no way
to avoid this; Python will overwrite the installation directory when upgrading
the InsightIQ package.

Example file structure before InsightIQ upgrade::

  insightiq
    \patches
      \patch-1234
      \patch-598
    \config
    \core
    features.py

Example file structure after InsightIQ upgrade::

  insightiq
    \config
    \core
    features.py

This simplifies upgrades because we A) don't have to try an "re-apply" a patch
after an upgrade, or B) update our list of installed patches after an upgrade.

Specific patch directory contents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Lets say we have patch-1234 installed. The directory created (which is used to
reference the patch) contains the following::

  \patch-1234
    meta.ini
    README.txt
    \originals

The ``meta.ini`` and ``README.txt`` are defined in the next section, and come from the
tar patch file. The directory ``originals`` contains backup copies of the original
source files. When you install a patch, the patching tool creates these backups
to enable us to uninstall the patch. Within that directory, you'll see some rather
long file names::

  \originals
    insightiq__controllers__security.py

The double-underbars ``__`` are used to replace the forward slash normally associated
with a file system path. A double-underbar is used instead of a single-underbar
because it's common for a Python source file to contain a single-underbar.

What's in a patch
-----------------

A patch for InsightIQ is a `tar file <https://en.wikipedia.org/wiki/Tar_(computing)>`_
consisting of the following files:

README.txt
  A description of the patch. This must always include the bug number for the
  issue that requires patching.

meta.ini
  A config file that defines what source files are getting patched, and what
  versions of InsightIQ the patch works with.

PATCHED_FILE
  The patched source file, where PATCHED_FILE is actually the name of
  the source file. There can be as many as these files as needed for the patch.

Within the tar file, these files must be stored in a directory that names the
patch following the convention of patch-PATCH_NUMBER, where PATCH_NUMBER is the
actual number used to identify the patch for Isilon. In other words, if you
unfurl the patch tar file, a directory with the patch files is written to your
file system.

Example of patch file contents::

    README.txt
    meta.ini
    insightiq/controllers/security.py


The meta.ini
^^^^^^^^^^^^

The format is your standard `INI file <https://en.wikipedia.org/wiki/INI_file>`_,
with the headings ``info``, ``version`` and ``files``.

The ``info`` heading has two keys, ``name`` which is the name of the patch, and
``bug`` which is the number for the associated bug that is being patched.

The ``versions`` heading has two keys, ``minimum`` and ``maximum``, and as you've
likely guessed, define the oldest and newest versions of InsightIQ that the patch
applies to.

The ``files`` heading defines what files are being patched, and can have as many
keys as necessary. The key names should be the location of the original source
file (relative to the installation directory), and the key values are the md5
hash of that original source file. Why are we including md5 hashes? To avoid
installing patches that clobber (i.e. patch B overwrites the same file as patch A).

Example meta.ini::

  [info]
  name = patch-1234
  bug = 156986
  [version]
  minimum = 4.1.0
  maximum = 4.1.1
  [files]
  insightiq/controllers/security.py = 56266031a30cab220f56ee43b4159ded

.. note::

    Version values are inclusive. If your patch *only* applies to one specific
    release, both ``minimum`` and ``maximum`` should have the same value.


Making a patch
==============

There are the steps to create a patch for a single source file.
In this example, we are patching insightiq/controllers/security.py

1. Create a directory for the patch::

    $ mkdir patch-1234

#. Copy your README.txt and meta.ini files into the directory made in step 1::

    $ cp README.txt meta.ini patch-1234

#. Create all subdirectories for the source file paths::

    $ mkdir -p patch-1234/insightiq/controllers

# Copy the patched files unto their respective locations:::

    $ cp security.py patch-1234/insightiq/controllers/

#. Create the tgz file::

    $ cd patch-1234 && tar -zcvf insightiq-patch-1234.tgz *
