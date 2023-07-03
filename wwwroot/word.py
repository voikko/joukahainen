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

# This file contains the word editor

import sys
import gettext
import joheaders
import jotools
import joeditors
import jodb
from functools import reduce

_ = gettext.gettext

# Returns a html class selector for a list of classes in form (cid, description). If cid != None,
# then that class is already selected (as a hidden field). Row is the number of editable row
# in the table. If include_no_class is True, then it will be possible to choose class 0
# (invalid word).
def get_class_selector(classlist, cid, row, include_no_class):
	if cid == None and row != -1:
		retstr = ''
		for res in classlist:
			retstr = retstr + ('<label class="nobr"><input type="radio" name="class%i" ' +
			                   'value="%i">%s</input></label>') \
			         % (row, res[0], jotools.escape_html(res[1]))
		if include_no_class:
			retstr = retstr + ('<label class="nobr"><input type="radio" name="class%i" ' +
			    'value="0">%s</input></label>') % (row, _('reject'))
		return retstr
	else:
		for res in classlist:
			if res[0] == cid:
				return ('<input type="hidden" name="class%i" value="%i" />' +
			                  '%s') % (row, cid,
				        jotools.escape_html(res[1]))
		return '&nbsp;'

# Writes a table body for entering new words. If words != None, the table is initialised with the given
# list of words. Otherwise empty list is written, with the number of rows taken from parameter 'count'.
def add_entry_fields(req, db, words = None, count = 1):
	class_res = db.query("select classid, name from wordclass").getresult()
	if words == None:
		for i in range(count):
			jotools.write(req, '<tr><td><input type="text" name="word%i" /></td><td>' % i)
			for res in class_res:
				jotools.write(req, ('<label><input type="radio" name="class%i" ' +
				                     'value="%i">%s</input></label>\n') \
				            % (i, res[0], jotools.escape_html(res[1])))
			jotools.write(req, '</td></tr>\n')
		return
	confirm_column = False
	for word in words:
		if word['try_again'] == True:
			confirm_column = True
			break
	i = 0
	for word in words:
		jotools.write(req, '<tr><td>')
		if word['try_again']:
			if word['oword'] != None:
				jotools.write(req, '<input type="hidden" name="origword%i" value=%s />' \
				                   % (i, jotools.escape_form_value(word['oword'])))
			jotools.write(req, '<input type="hidden" name="word%i" value=%s />%s</td><td>' \
			                   % (i, jotools.escape_form_value(word['word']), 
				               jotools.escape_html(word['word'])))
			incnocls = word['oword'] != None
			jotools.write(req, get_class_selector(class_res, word['cid'], i, incnocls))
			jotools.write(req, '<td><input type="checkbox" name="confirm%i"></td><td>' % i)
			jotools.write(req, word['error'])
			jotools.write(req, '</td>')
			i = i + 1
		else:
			jotools.write(req, jotools.escape_html(word['word']))
			jotools.write(req, '</td><td>')
			jotools.write(req, get_class_selector(class_res, word['cid'], -1, False))
			jotools.write(req, '</td><td>')
			if confirm_column: jotools.write(req, '&nbsp;</td><td>')
			jotools.write(req, word['error'])
			jotools.write(req, '</td>')
		jotools.write(req, '</tr>\n')

# Returns a list of links for all of the homonyms of given word.
def _list_homonyms(db, word):
	res = db.query("SELECT w.wid, w.word, wc.name FROM word w, wordclass wc " +
		      "WHERE w.class = wc.classid AND w.word = $1", (word,))
	h = ''
	for r in res.getresult():
		h = h + '<a href="edit?wid=%i">%s(%s)</a> ' \
		    % (r[0], jotools.escape_html(r[1]),
		       jotools.escape_html(r[2]))
	if len(h) == 0: return ''
	else: return _('Homonyms') + ': ' + h

# Stores a new word into the database and marks the original in raw_words as processed
# (if needed). Returns (wid, add_entry_structure) where wid is the identifier for
# the new word (or None if nothing was added) and add_entry_structure is a tuple
# for _add_entry containing the description of a word that needs confirmation from
# user before being added (or None if no confirmation is needed).
#def _store_word(db, word, oword, wclass, dupl_confirmed, uid):
def store_word(db, word, uid):
	if word['try_again'] == False: return word
	retval = {'word': word['word'], 'oword': word['oword'], 'cid': word['cid'], 'confirmed': False,
	          'wid': None, 'error': None}
	if not jotools.checkword(word['word']):
		retval['wid'] = None
		retval['error'] = _('Forbidden characters in the word')
		retval['try_again'] = False
		return retval
	if word['cid'] == None:
		retval['wid'] = None
		retval['error'] = _('Word class must be set')
		retval['try_again'] = True
		return retval
	if word['cid'] != 0:
		if not word['confirmed']:
			homonyms = _list_homonyms(db, word['word'])
			if len(homonyms) > 0:
				retval['wid'] = None
				retval['error'] = homonyms
				retval['try_again'] = True
				return retval
		retval['wid'] = db.query("SELECT nextval('word_wid_seq')").getresult()[0][0]
		db.query("INSERT INTO word(wid, word, class, cuser) VALUES($1, $2, $3, $4)", \
		          (retval['wid'], retval['word'], retval['cid'], uid))
		retval['error'] = '<a href="edit?wid=%i">%s</a>' % (retval['wid'], _('Word added'))
	if word['oword'] != None:
		db.query("UPDATE raw_word SET processed = TRUE WHERE word = $1", (word['oword'],))
		if retval['error'] == None:
			retval['error'] = _('Word removed from the list of candidate words')
	retval['try_again'] = False
	if retval['error'] == None: retval['error'] = _('Nothing was done')
	return retval
