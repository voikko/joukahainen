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

def login_logout(db, uid, uname, wid):
	if uid == None:
		return u"""
<form method="post" action="%s/user/login"><p>
<label>Käyttäjätunnus: <input type="text" name="username" /></label>&nbsp;
<label>Salasana: <input type="password" name="password" /></label>&nbsp;
<input type="hidden" name="wid" value="%i" />
<input type="submit" value="Kirjaudu sisään" />
</p></form>
""" % (_config.WWW_ROOT_DIR, wid)
	return u"""
<form method="post" action="%s/user/logout"><p>
<input type="hidden" name="wid" value="%i" />
<input type="submit" value="Kirjaa ulos käyttäjä %s" />
</p></form>
""" % (_config.WWW_ROOT_DIR, wid, uname)

def call(db, funcname, paramlist):
	if funcname == 'login_logout':
		if len(paramlist) != 3: return u"Error: 3 parameter expected"
		return login_logout(db, paramlist[0], paramlist[1], paramlist[2])
	return u"Error: unknown function"
