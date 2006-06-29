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

# This file contains database related helper functions

import _pg
import _config

def connect():
	return _pg.connect(
		host=_config.DBHOST,
		dbname=_config.DB_PUBLIC_DATABASE,
		port=_config.DB_PORT,
		user=_config.DB_USER,
		passwd=_config.DB_PASSWORD)

def connect_private():
	return _pg.connect(
		host=_config.DBHOST,
		dbname=_config.DB_PRIVATE_DATABASE,
		port=_config.DB_PORT,
		user=_config.DB_USER,
		passwd=_config.DB_PASSWORD)
