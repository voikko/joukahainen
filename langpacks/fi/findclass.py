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

# This file contains tools to find inflection class for a word

from mod_python import apache

import sys
import _config
import _apply_config
import hfaffix
import hfutils
import joheaders
import jotools
import jooutput
import jodb


CHARACTERISTIC_NOUN_FORMS = ['nominatiivi', 'genetiivi', 'partitiivi', 'illatiivi',
                             'genetiivi_mon', 'partitiivi_mon', 'illatiivi_mon']
CHARACTERISTIC_VERB_FORMS = ['infinitiivi_1', 'preesens_yks_1', 'imperfekti_yks_3',
                             'kondit_yks_3', 'imperatiivi_yks_3', 'partisiippi_2',
                             'imperfekti_pass']
def classlist(req):
	joheaders.page_header(req, u'Etsi sanalle taivutusluokka')
	jotools.write(req, u'''
<form method="get" action="classlist"><p>
<label>Sana: <input type="text" name="word" /><br />
Sanaluokka: <select name="class">
<option selected="1" value="1">Nomini</option>
<option value="3">Verbi</option>
</select><br />
Astevaihteluluokka: <select name="gclass">
<option selected="1" value="">ei astevaihtelua</option>
<option value="av1">av1</option>
<option value="av2">av2</option>
<option value="av3">av3</option>
<option value="av4">av4</option>
<option value="av5">av5</option>
<option value="av6">av6</option>
</select><br />
<input type="submit" value="Hae mahdolliset taivutukset"></p>
</form>''')
	classid = jotools.toint(jotools.get_param(req, 'class', u'0'))
	if classid == 1:
		classdatafile = _config.HF_DATA + "/subst.aff"
		characteristic_forms = CHARACTERISTIC_NOUN_FORMS
	elif classid == 3:
		classdatafile = _config.HF_DATA + "/verb.aff"
		characteristic_forms = CHARACTERISTIC_VERB_FORMS
	elif classid == 0:
		joheaders.page_footer(req)
		return "</html>"
	else:
		joheaders.error_page(req, u'Sanaluokkaa ei ole olemassa')
		return '\n'
	
	word = jotools.get_param(req, 'word', u'')
	grad_type = jotools.get_param(req, 'gclass', u'')
	if grad_type == u'':
		grad_type_s = u''
		grad_type = u'-'
	else:
		grad_type_s = u'-' + grad_type
	
	word_classes = hfaffix.read_word_classes(classdatafile)
	
	for word_class in word_classes:
		if len(word_class['smcnames']) == 0: continue
		inflected_words = hfaffix.inflect_word(word, grad_type, word_class)
		if inflected_words == None: continue
		form = None
		inflist = []
		inflected_words.append((u'', u'', u''))
		jotools.write(req, '<h2>' + word_class['smcnames'][0] + grad_type_s + '</h2>')
		jotools.write(req, u'<br /><table class="border">\n')
		for inflected_word in inflected_words:
			if form != inflected_word[0]:
				if form != None and len(inflist) > 0:
					if form in characteristic_forms or form[0] == u'!':
						if form[0] == u'!':
							form = form[1:]
						infs = reduce(lambda x, y: u"%s, %s" % (x, y), inflist)
						jotools.write(req, (u"<tr><td>%s</td><td>%s</td></tr>\n" %
						          (form, infs)))
				inflist = []
				form = inflected_word[0]
			if hfutils.read_option(inflected_word[2], 'ps', '-') != 'r' \
			   and not inflected_word[1] in inflist:
				inflist.append(inflected_word[1])
		jotools.write(req, u'</table>\n')
	
	joheaders.page_footer(req)
	return "</html>"
