# -*- coding: utf-8 -*-

# Copyright 2006 - 2023 Harri Pitkänen (hatapitk@iki.fi)
# This file is part of Joukahainen, a vocabulary management application

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This file contains html headers, footers and related functions

import _config
import jotools

_ = _config.transl

# Outputs the shared header for a page with no navigation bar
def page_header_nonavbar(req, title):
	req.content_type = "text/html; charset=UTF-8"
	req.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fi" lang="fi">
<head>
<title>%s</title>
<link rel="stylesheet" type="text/css" href="%s/style.css" />
<link rel="icon" type="image/png" href="%s/joukahainen-small.png" />
<script type="text/javascript" src="%s/jscripts.js"></script>
</head>
<body onload="initPage()">
<div class="main">
""" % (title, _config.WWW_ROOT_DIR, _config.WWW_ROOT_DIR,
                              _config.WWW_ROOT_DIR))

# Outputs the shared html header for ordinary pages
def _page_header_internal(req, title, h1, uid, uname, wid):
	req.content_type = "text/html; charset=UTF-8"
	jotools.write(req, """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fi" lang="fi">
<head>
<title>%s</title>
<link rel="stylesheet" type="text/css" href="%s/style.css" />
<link rel="icon" type="image/png" href="%s/joukahainen-small.png" />
<link rel="search" type="application/opensearchdescription+xml"
 title="Joukahainen" href="%s/searchplugin-fullsearch-re.xml" />
<script type="text/javascript" src="%s/jscripts.js"></script>
</head>
<body onload="initPage()">
<div class="topbar">""" % (title, _config.WWW_ROOT_DIR, _config.WWW_ROOT_DIR,
                           _config.WWW_ROOT_DIR, _config.WWW_ROOT_DIR))
	jotools.write(req, "\n<h1>%s</h1>" % h1)
	if uid == None:
		jotools.write(req, """
<div class="login">
<form method="post" action="%s/user/login"><p>
<label>%s: <input type="text" size="12" name="username" /></label>&nbsp;
<label>%s: <input type="password" size="12" name="password" /></label>&nbsp;
<input type="hidden" name="wid" value="%i" />
<input type="submit" value="%s" />
</p></form>
</div>
""" % (_config.WWW_ROOT_DIR, _('Username'), _('Password'), wid, _('Log in')))
	else:
		jotools.write(req, """
<div class="login">
<form method="post" action="%s/user/logout"><p>
<input type="hidden" name="wid" value="%i" />
<input type="submit" value="%s %s" />
</p></form>
</div>
""" % (_config.WWW_ROOT_DIR, wid, _('Log out user'), uname))
	jotools.write(req, '<div class="clear"></div></div><div class="main">\n')

# Outputs the shared html header for toplevel page
def page_header_navbar_level0(req, title, uid, uname):
	title = jotools.escape_html(title)
	h1 = title
	_page_header_internal(req, title, h1, uid, uname, 0)

# Outputs the shared html header for level 1 subpage
def page_header_navbar_level1(req, title, uid, uname, wid = 0):
	title = jotools.escape_html(title)
	h1 = '<a href="..">Joukahainen</a> &gt; %s' % title
	_page_header_internal(req, title, h1, uid, uname, wid)

# Outputs the shared html header for level 2 subpage
def page_header_navbar_level2(req, title1, link1, title2, uid, uname, wid = 0):
	title1 = jotools.escape_html(title1)
	title2 = jotools.escape_html(title2)
	title = title1 + ' &gt; ' + title2
	h1 = '<a href="..">Joukahainen</a> &gt; <a href="%s">%s</a> &gt; %s' % (link1, title1, title2)
	_page_header_internal(req, title, h1, uid, uname, wid)

# Outputs the shared frameset header
def frame_header(req, title):
	req.content_type = "text/html; charset=UTF-8"
	req.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fi" lang="fi">
<head>
<title>%s</title>
<link rel="stylesheet" type="text/css" href="%s/style.css" />
</head>
""" % (title.encode('UTF-8'), _config.WWW_ROOT_DIR))

# Ordinary shared page footer
def page_footer_plain(req):
	req.write("""
</div>
</body>
</html>""")

# Outputs the shared frameset footer
def frame_footer(req):
	req.write('\n</html>')

# Outputs a page with automatic redirection to another location
def redirect_header(req, location):
	location_s = location.encode('UTF-8')
	req.headers_out['location'] = location_s
	req.status = jotools.HTTP_MOVED_PERMANENTLY
	jotools.write(req, _("Redirecting to %s") % location_s)

# Outputs a page containing error message
def error_page(req, errortext):
	page_header_nonavbar(req, 'Joukahainen: %s' % _('error'))
	jotools.write(req, '<h1>%s</h1><p>%s</p>\n' % (_('Error'), errortext))
	page_footer_plain(req)

# Outputs a page telling about successful operation
def ok_page(req, message):
	page_header_nonavbar(req, 'Joukahainen: %s' % _('operation succeeded'))
	jotools.write(req, '<h1>%s</h1><p>%s</p>\n' % (_('operation succeeded'), message))
	jotools.write(req, '<p><a href="%s">%s ...</a></p>\n' \
	           % (_config.WWW_ROOT_DIR + '/', _('Back to front page')))
	page_footer_plain(req)
