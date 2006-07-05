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

def page_header(req, title):
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
""" % (title.encode('UTF-8'), _config.WWW_ROOT_DIR, _config.WWW_ROOT_DIR))


def page_footer(req):
	req.write('\n</body>')

def redirect_header(req, location):
	location_s = location.encode('UTF-8')
	req.headers_out['location'] = location_s
	req.status = mod_python.apache.HTTP_MOVED_TEMPORARILY
	req.send_http_header()
	req.write("Redirecting to %s" % location_s)

def error_page(req, errortext):
	page_header(req, u'Joukahainen: virhe')
	req.write((u'<h1>Virhe</h1><p>%s</p>\n' % errortext).encode('UTF-8'))
	page_footer(req)
