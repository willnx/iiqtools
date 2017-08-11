#######
Scripts
#######

This directory should only contain the script that get installed onto the
InsightIQ appliance.

Scripts should only contain entry point logic, and configure any paths for
dependency resolution. If your script depends on a module that is packaged
within the InsightIQ virtualenv, you'll have to add this to the top of the script::

  #!/usr/share/isilon/bin/python
  """
  <Some handy documentation of what your script does here>
  """
  import sys
  # Dirty hack so we can import modules from the InsightIQ virtualenv
  # Two additions to path because InsightIQ might be running Python 2.6 or 2.7
  # The insert makes Python look at the IIQ virtualenv 1st; otherwise we'll get
  # package version conflicts when trying to resolve dependencies for IIQ modules.
  sys.path.insert(1, '/usr/share/isilon/lib/python2.6/site-packages')
  sys.path.insert(1, '/usr/share/isilon/lib/python2.7/site-packages')
