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

# This file contains functions that output official Malaga lexicon files
# for Voikko.

from mod_python import apache

import sys
import _config
import _apply_config
import functions
import jodb
import jotools

# The default vocabulary
def default(req):
	query = u"""
SELECT wd.wid, wd.class, wd.word
FROM word wd
WHERE wd.wid NOT IN (
  SELECT wid FROM flag_attribute_value
  WHERE aid IN (15, 19, 33, 24, 26, 35)
)"""
	db = jodb.connect()
	functions.jooutput_call(req, 'malaga', db, query)
	return '\n'

# Special vocabulary
def special(req):
	aid = jotools.toint(jotools.get_param(req, 'aid', u'0'))
	query = u"""
SELECT wd.wid, wd.class, wd.word
FROM word wd, flag_attribute_value a1
WHERE wd.wid = a1.wid AND a1.aid = %i
AND wd.wid NOT IN (
  SELECT wid FROM flag_attribute_value a2
  WHERE a2.aid IN (24, 26)
)""" % aid
	db = jodb.connect()
	functions.jooutput_call(req, 'malaga', db, query)
	return '\n'
