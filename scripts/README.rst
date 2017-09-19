#######
Scripts
#######

This directory should only contain the script that get installed onto the
InsightIQ appliance.

Scripts should only contain entry point logic, and then run your *main* function.

Example::

  #!/usr/bin/python
  """
  <Some handy documentation of what your script does here>
  """
  import sys

  from iiqtool.YOUR_MODULE import main


  if __name__ == '__main__':
      sys.exit(main(sys.argv[1:]))
