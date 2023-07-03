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

# This file contains index page components

import types
import _config
import gettext

_ = gettext.gettext

def login_logout(db, uid, uname, wid):
	if uid == None:
		return """
<form method="post" action="%s/user/login"><p>
<label>%s: <input type="text" name="username" /></label>&nbsp;
<label>%s: <input type="password" name="password" /></label>&nbsp;
<input type="hidden" name="wid" value="%i" />
<input type="submit" value="%s" />
</p></form>
""" % (_config.WWW_ROOT_DIR, _('Username'), _('Password'), wid, _('Log in'))
	return """
<form method="post" action="%s/user/logout"><p>
<input type="hidden" name="wid" value="%i" />
<input type="submit" value="%s %s" />
</p></form>
""" % (_config.WWW_ROOT_DIR, wid, _('Log out user'), uname)

def call(db, funcname, paramlist):
	if funcname == 'login_logout':
		if len(paramlist) != 3: return _("Error: % parameters expected" % 3)
		return login_logout(db, paramlist[0], paramlist[1], paramlist[2])
	return _("Error: unknown function")
