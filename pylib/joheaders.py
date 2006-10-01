# -*- coding: utf-8 -*-

# Copyright 2006 Harri Pitkänen (hatapitk@iki.fi)
# This file is part of Joukahainen, a vocabulary management application

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# This file contains html headers, footers and related functions

import mod_python.apache
import _config
import _apply_config
import jotools
import joindex

_ = _apply_config.translation.ugettext

# Outputs the shared header for a page with no navigation bar
def page_header_nonavbar(req, title):
	req.content_type = "text/html; charset=UTF-8"
	req.send_http_header()
	req.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head>
<title>%s</title>
<link rel="stylesheet" type="text/css" href="%s/style.css" />
<script type="text/javascript" src="%s/jscripts.js"></script>
</head>
<body onload="initPage()">
<div class="main">
""" % (title.encode('UTF-8'), _config.WWW_ROOT_DIR, _config.WWW_ROOT_DIR))

# Outputs the shared html header for ordinary pages
def _page_header_internal(req, title, h1, uid, uname, wid):
	req.content_type = "text/html; charset=UTF-8"
	req.send_http_header()
	jotools.write(req, u"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head>
<title>%s</title>
<link rel="stylesheet" type="text/css" href="%s/style.css" />
<script type="text/javascript" src="%s/jscripts.js"></script>
</head>
<body onload="initPage()">
<div class="topbar">""" % (title, _config.WWW_ROOT_DIR, _config.WWW_ROOT_DIR))
	jotools.write(req, u"\n<h1>%s</h1>" % h1)
	if uid == None:
		jotools.write(req, u"""
<div class="login">
<form method="post" action="%s/user/login"><p>
<label>%s: <input type="text" name="username" /></label>&nbsp;
<label>%s: <input type="password" name="password" /></label>&nbsp;
<input type="hidden" name="wid" value="%i" />
<input type="submit" value="%s" />
</p></form>
</div>
""" % (_config.WWW_ROOT_DIR, _(u'Username'), _(u'Password'), wid, _(u'Log in')))
	else:
		jotools.write(req, u"""
<div class="login">
<form method="post" action="%s/user/logout"><p>
<input type="hidden" name="wid" value="%i" />
<input type="submit" value="%s %s" />
</p></form>
</div>
""" % (_config.WWW_ROOT_DIR, wid, _(u'Log out user'), uname))
	jotools.write(req, u'<div class="clear"></div></div><div class="main">\n')

# Outputs the shared html header for toplevel page
def page_header_navbar_level0(req, title, uid, uname):
	title = jotools.escape_html(title)
	h1 = title
	_page_header_internal(req, title, h1, uid, uname, 0)

# Outputs the shared html header for level 1 subpage
def page_header_navbar_level1(req, title, uid, uname, wid = 0):
	title = jotools.escape_html(title)
	h1 = u'<a href="..">Joukahainen</a> &gt; %s' % title
	_page_header_internal(req, title, h1, uid, uname, wid)

# Outputs the shared html header for level 2 subpage
def page_header_navbar_level2(req, title1, link1, title2, uid, uname, wid = 0):
	title1 = jotools.escape_html(title1)
	title2 = jotools.escape_html(title2)
	title = title1 + u' &gt; ' + title2
	h1 = u'<a href="..">Joukahainen</a> &gt; <a href="%s">%s</a> &gt; %s' % (link1, title1, title2)
	_page_header_internal(req, title, h1, uid, uname, wid)

def frame_header(req, title):
	req.content_type = "text/html; charset=UTF-8"
	req.send_http_header()
	req.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">
<html>
<head>
<title>%s</title>
<link rel="stylesheet" type="text/css" href="%s/style.css" />
</head>
""" % (title.encode('UTF-8'), _config.WWW_ROOT_DIR))

def page_footer(req):
	req.write('\n</body>')

def frame_footer(req):
	req.write('\n</html>')

def redirect_header(req, location):
	location_s = location.encode('UTF-8')
	req.headers_out['location'] = location_s
	req.status = mod_python.apache.HTTP_MOVED_TEMPORARILY
	req.send_http_header()
	jotools.write(req, _(u"Redirecting to %s") % location_s)

def error_page(req, errortext):
	page_header(req, u'Joukahainen: %s' % _(u'error'))
	jotools.write(req, u'<h1>%s</h1><p>%s</p>\n' % (_(u'Error'), errortext))
	page_footer(req)

def ok_page(req, message):
	page_header(req, u'Joukahainen: %s' % _(u'operation succeeded'))
	jotools.write(req, u'<h1>%s</h1><p>%s</p>\n' % (_(u'operation succeeded'), message))
	jotools.write(req, u'<p><a href="%s">%s ...</a></p>\n' \
	           % (_config.WWW_ROOT_DIR + '/', _(u'Back to front page')))
	page_footer(req)
	req.write('\n</html>')

def list_page_header(req, headertext, uid, uname):
	page_header(req, headertext)
	jotools.write(req, u"""<div class="topbar">
<h1>%s</h1>
<div class="login">%s</div>
<div class="clear"></div>
</div>
<div class="main">""" % (headertext, joindex.login_logout(None, uid, uname, 0)))

def list_page_footer(req):
	jotools.write(req, u"</div>\n")
	page_footer(req)
