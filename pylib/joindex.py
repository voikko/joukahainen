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

# This file contains index page components

import hfaffix
import hfutils
import types
import _config
import _apply_config

_ = _apply_config.translation.ugettext

def login_logout(db, uid, uname, wid):
	if uid == None:
		return u"""
<form method="post" action="%s/user/login"><p>
<label>%s: <input type="text" name="username" /></label>&nbsp;
<label>%s: <input type="password" name="password" /></label>&nbsp;
<input type="hidden" name="wid" value="%i" />
<input type="submit" value="%s" />
</p></form>
""" % (_config.WWW_ROOT_DIR, _(u'Username'), _(u'Password'), wid, _(u'Log in'))
	return u"""
<form method="post" action="%s/user/logout"><p>
<input type="hidden" name="wid" value="%i" />
<input type="submit" value="%s %s" />
</p></form>
""" % (_config.WWW_ROOT_DIR, wid, _(u'Log out user'), uname)

def call(db, funcname, paramlist):
	if funcname == 'login_logout':
		if len(paramlist) != 3: return _(u"Error: % parameters expected" % 3)
		return login_logout(db, paramlist[0], paramlist[1], paramlist[2])
	return _(u"Error: unknown function")
