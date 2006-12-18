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

# This file contains the common initialisation code for the application

import sys
import gettext
import _config

sys.path.append(_config.INSTALLATION_DIRECTORY + u'/langpacks/' + _config.LANG)
sys.path.append(_config.INSTALLATION_DIRECTORY + u'/pylib')
translation = gettext.translation(u'joukahainen', _config.INSTALLATION_DIRECTORY + u'/transl',
                                  [_config.LANG], fallback=True)

_ = translation.ugettext

import functions

jotools_checkword = functions.checkword
jooutput_list_supported_types = functions.jooutput_list_supported_types
jooutput_call = functions.jooutput_call


def _default_word_inflection(db, wid, word, classid):
	return u"(%s)" % _(u"Inflections are not available for this language")

if hasattr(functions, 'word_inflection'): joeditors_word_inflection = functions.word_inflection
else: joeditors_word_inflection = _default_word_inflection


def _default_kotus_class(db, wid, classid):
	return u"(%s)" % _(u"Kotus class is not available for this language")

if hasattr(functions, 'kotus_class'): joeditors_kotus_class = functions.kotus_class
else: joeditors_kotus_class = _default_kotus_class


def _default_find_infclass(db, word, classid):
	return None

if hasattr(functions, 'find_infclass'): joeditors_find_infclass = functions.find_infclass
else: joeditors_find_infclass = _default_find_infclass
