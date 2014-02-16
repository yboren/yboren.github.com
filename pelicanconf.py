#!/usr/bin/env python2
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'yboren'
SITENAME = u'Linux Notes'
SITEURL = ''

TIMEZONE = 'Asia/Shanghai'

DEFAULT_LANG = u'zh'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None

# Blogroll
LINKS =  (('Pelican', 'http://getpelican.com/'),
          )

# Social widget
#SOCIAL = (('You can add links in your config file', '#'),
#          ('Another social link', '#'),)

DEFAULT_PAGINATION = 10
SUMMARY_MAX_LENGTH = 50

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

#plugins
PLUGIN_PATH = "plugins"
#PLUGINS = ["list", "of", "plugins"]

#static files
STATIC_PATHS = ["images",]
