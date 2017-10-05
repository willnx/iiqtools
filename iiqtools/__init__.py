# -*- coding: UTF-8 -*-

# Well, you might be wondering what the hell we're doing in this file.
# The short answer is hacking on sys.path so Python can find the few packages
# in InsightIQ used by IIQTools. Yes, I know, not the most elegant solution; simply
# installing those dependencies would be the "right way" to do this, but that's not
# possible here. InsightIQ is closed source. In addition, installing everything
# except InsightIQ (to cut down on the path hacking) doesn't work for all our
# users; some have no access to the Internet, thus they'd have to manually install
# all these packages.
# The path hacking is happening here because this __init__ will alway be evaluated
# when importing anything from IIQTools. The only other option would be to add
# the path hacks to *every* script, which is a far worse idea. The great news is
# that unless you've stumbled upon this file, you'd never have known about it;
# everything should "just work" as far as importing packages goes.
import sys

IIQ_PATHS = ['/usr/share/isilon/lib/python2.6/site-packages/argparse-1.2.1-py2.6.egg',
             '/usr/share/isilon/lib/python2.6/site-packages/python_cjson-1.0.5-py2.6-linux-x86_64.egg',
             '/usr/share/isilon/lib/python2.6/site-packages/Paste-1.7.5.1-py2.6.egg',
             '/usr/share/isilon/lib/python2.6/site-packages/PasteDeploy-1.3.3-py2.6.egg',
             '/usr/share/isilon/lib/python2.6/site-packages/Pylons-1.0-py2.6.egg',
             '/usr/share/isilon/lib/python2.6/site-packages/WebHelpers-0.6.4-py2.6.egg',
             '/usr/share/isilon/lib/python2.6/site-packages/dnspython-1.8.0-py2.6.egg',
             '/usr/share/isilon/lib/python2.6/site-packages/psycopg2-2.5.4-py2.6-linux-x86_64.egg',
             '/usr/share/isilon/lib/python2.6/site-packages/python_cjson-1.0.5-py2.6-linux-x86_64.egg',
             '/usr/share/isilon/lib/python2.6/site-packages/pytz-2015.2-py2.6.egg',
             '/usr/share/isilon/lib/python2.6/site-packages/configobj-4.7.2-py2.6.egg',
]

sys.path.insert(1, '/usr/share/isilon/lib/python2.6/site-packages')
sys.path.insert(1, '/usr/share/isilon/lib/python2.7/site-packages')
sys.path += IIQ_PATHS
