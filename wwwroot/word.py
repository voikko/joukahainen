# -*- coding: utf-8 -*-

# Copyright 2006 - 2009 Harri Pitkänen (hatapitk@iki.fi)
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

from mod_python import apache

import sys
import random
import _apply_config
import _config
import joheaders
import jotools
import joeditors
import jodb
from functools import reduce

_ = _apply_config.translation.ugettext


# Returns a html class selector for a list of classes in form (cid, description). If cid != None,
# then that class is already selected (as a hidden field). Row is the number of editable row
# in the table. If include_no_class is True, then it will be possible to choose class 0
# (invalid word).
def _get_class_selector(classlist, cid, row, include_no_class):
	if cid == None and row != -1:
		retstr = ''
		for res in classlist:
			retstr = retstr + ('<label class="nobr"><input type="radio" name="class%i" ' +
			                   'value="%i">%s</input></label>') \
			         % (row, res[0], jotools.escape_html(str(res[1], 'UTF-8')))
		if include_no_class:
			retstr = retstr + ('<label class="nobr"><input type="radio" name="class%i" ' +
			    'value="0">%s</input></label>') % (row, _('reject'))
		return retstr
	else:
		for res in classlist:
			if res[0] == cid:
				return ('<input type="hidden" name="class%i" value="%i" />' +
			                  '%s') % (row, cid,
				        jotools.escape_html(str(res[1], 'UTF-8')))
		return '&nbsp;'

# Writes a table body for entering new words. If words != None, the table is initialised with the given
# list of words. Otherwise empty list is written, with the number of rows taken from parameter 'count'.
def _add_entry_fields(req, db, words = None, count = 1):
	class_res = db.query("select classid, name from wordclass").getresult()
	if words == None:
		for i in range(count):
			jotools.write(req, '<tr><td><input type="text" name="word%i" /></td><td>' % i)
			for res in class_res:
				jotools.write(req, ('<label><input type="radio" name="class%i" ' +
				                     'value="%i">%s</input></label>\n') \
				            % (i, res[0], jotools.escape_html(str(res[1], 'UTF-8'))))
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
			jotools.write(req, _get_class_selector(class_res, word['cid'], i, incnocls))
			jotools.write(req, '<td><input type="checkbox" name="confirm%i"></td><td>' % i)
			jotools.write(req, word['error'])
			jotools.write(req, '</td>')
			i = i + 1
		else:
			jotools.write(req, jotools.escape_html(word['word']))
			jotools.write(req, '</td><td>')
			jotools.write(req, _get_class_selector(class_res, word['cid'], -1, False))
			jotools.write(req, '</td><td>')
			if confirm_column: jotools.write(req, '&nbsp;</td><td>')
			jotools.write(req, word['error'])
			jotools.write(req, '</td>')
		jotools.write(req, '</tr>\n')

# Returns a list of links for all of the homonyms of given word.
def _list_homonyms(db, word):
	res = db.query(("SELECT w.wid, w.word, wc.name FROM word w, wordclass wc " +
		      "WHERE w.class = wc.classid AND w.word = '%s'") \
		      % jotools.escape_sql_string(word))
	h = ''
	for r in res.getresult():
		h = h + '<a href="edit?wid=%i">%s(%s)</a> ' \
		    % (r[0], jotools.escape_html(str(r[1], 'UTF-8')),
		       jotools.escape_html(str(r[2], 'UTF-8')))
	if len(h) == 0: return ''
	else: return _('Homonyms') + ': ' + h

# Stores a new word into the database and marks the original in raw_words as processed
# (if needed). Returns (wid, add_entry_structure) where wid is the identifier for
# the new word (or None if nothing was added) and add_entry_structure is a tuple
# for _add_entry containing the description of a word that needs confirmation from
# user before being added (or None if no confirmation is needed).
#def _store_word(db, word, oword, wclass, dupl_confirmed, uid):
def _store_word(db, word, uid):
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
		db.query("INSERT INTO word(wid, word, class, cuser) VALUES(%i, '%s', %i, %i)" \
		         % (retval['wid'], jotools.escape_sql_string(retval['word']),
		            retval['cid'], uid))
		retval['error'] = '<a href="edit?wid=%i">%s</a>' % (retval['wid'], _('Word added'))
	if word['oword'] != None:
		db.query("UPDATE raw_word SET processed = TRUE WHERE word = '%s'" \
		         % jotools.escape_sql_string(word['oword']))
		if retval['error'] == None:
			retval['error'] = _('Word removed from the list of candidate words')
	retval['try_again'] = False
	if retval['error'] == None: retval['error'] = _('Nothing was done')
	return retval

def add_from_db(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, _('You are not allowed to edit data'))
		return '\n'
	if req.method != 'GET':
		joheaders.error_page(req, _('Only GET requests are allowed'))
		return '\n'
	db = jodb.connect()
	words_per_page = 15
	category = jotools.get_param(req, 'category', None)
	if category == None: condition = ""
	else: condition = "AND coalesce(info, '') = '%s'" \
	                  % jotools.escape_sql_string(category)
	results = db.query("SELECT count(*) FROM raw_word WHERE processed = FALSE %s" \
	                   % condition)
	nwords = results.getresult()[0][0]
	if nwords <= words_per_page: limit = ""
	else: limit = "LIMIT %i OFFSET %i" % (words_per_page,
	              random.randint(0, nwords - words_per_page))
	results = db.query(("SELECT word, coalesce(notes, '') FROM raw_word " +
	                    "WHERE processed = FALSE %s " +
	                    "ORDER BY word %s") % (condition, limit))
	if results.ntuples() == 0 and category == None:
		joheaders.error_page(req, _('There are no words to be added'))
		return '\n'
	if results.ntuples() == 0 and category != None:
		joheaders.error_page(req, _('There are no words to be added') + ' ' +
		          _('in category %s') % jotools.escape_html(category))
		return '\n'
	class_res = db.query("select classid, name from wordclass").getresult()
	joheaders.page_header_navbar_level1(req, _("Add words"), uid, uname)
	jotools.write(req, '<form method="post" action="add">\n')
	jotools.write(req, '<table class="border">\n')
	jotools.write(req, '<tr><th>%s</th><th>%s</th><th>%s</th></tr>\n' \
	                   % (_('Word'), _('Word class'), _('Notes')))
	i = 0
	for result in results.getresult():
		word = str(result[0], 'UTF-8')
		notes = str(result[1], 'UTF-8')
		jotools.write(req, '<tr><td><input type="hidden" name="origword%i" value=%s />' \
			                   % (i, jotools.escape_form_value(word)))
		jotools.write(req, '<input type="text" name="word%i" value=%s /></td><td>' \
		                   % (i, jotools.escape_form_value(word)))
		jotools.write(req, _get_class_selector(class_res, None, i, True))
		jotools.write(req, '</td><td>')
		jotools.write(req, jotools.escape_html(notes))
		jotools.write(req, '</td></tr>\n')
		i = i + 1
	jotools.write(req, '</table>\n' +
	                   '<p><input type="submit" value="%s"></p></form>\n' % _("Add words"))
	joheaders.page_footer_plain(req)
	return '\n'

def add_manual(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, _('You are not allowed to edit data'))
		return '\n'
	if req.method != 'GET':
		joheaders.error_page(req, _('Only GET requests are allowed'))
		return '\n'
	db = jodb.connect()
	words_per_page = 15
	joheaders.page_header_navbar_level1(req, _("Add words"), uid, uname)
	jotools.write(req, '<form method="post" action="add">\n' +
	                   '<table class="border">\n<tr><th>%s</th><th>%s</th></tr>\n' \
	                   % (_('Word'), _('Word class')))
	_add_entry_fields(req, db, None, words_per_page)
	jotools.write(req, '</table>\n' +
	                   '<p><input type="submit" value="%s"></p></form>\n' % _("Add words"))
	joheaders.page_footer_plain(req)
	return '\n'

def add(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, _('You are not allowed to edit data'))
		return '\n'
	db = jodb.connect()
	if req.method != 'POST':
		joheaders.error_page(req, _('Only POST requests are allowed'))
		return '\n'
	db.query("BEGIN")
	if jotools.get_param(req, 'confirm', '') == 'on': confirm = True
	else: confirm = False
	nwordlist = []
	added_count = 0
	need_confirm_count = 0
	i = -1
	while True:
		i = i + 1
		nword = jotools.get_param(req, 'word%i' % i, '')
		if nword == '': break
		word = {'word': nword, 'try_again': True, 'confirmed': False, 'wid': None}
		word['oword'] = jotools.get_param(req, 'origword%i' % i, None)
		nclass = jotools.get_param(req, 'class%i' % i, None)
		if not nclass in [None, '']: nclass = jotools.toint(nclass)
		else: nclass = None
		word['cid'] = nclass
		if confirm and nclass != 0 and jotools.get_param(req, 'confirm%i' % i, '') != 'on':
			word['error'] = _('Word was not added')
			word['try_again'] = False
		if jotools.get_param(req, 'confirm%i' % i, '') == 'on': word['confirmed'] = True
		stored_word = _store_word(db, word, uid)
		if stored_word['wid'] != None: added_count = added_count + 1
		if stored_word['try_again']: need_confirm_count = need_confirm_count + 1
		nwordlist.append(stored_word)
	db.query("COMMIT")
	if added_count == 1 and len(nwordlist) == 1:
		# No confirmation screen if exactly 1 word was successfully added
		joheaders.redirect_header(req, "edit?wid=%i" % nwordlist[0]['wid'])
		return '\n'
	joheaders.page_header_navbar_level1(req, _("Add words"), uid, uname)
	if need_confirm_count > 0:
		jotools.write(req, '<p>' + _('''Adding some words failed or requires confirmation.
Make the required changes and mark the words that you still want to add.''') + '</p>')
		jotools.write(req, '<form method="post" action="add">\n')
		jotools.write(req,
		  '<table class="border"><tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>\n' \
		  % (_('Word'), _('Word class'), _('Confirm addition'), _('Notes')))
		_add_entry_fields(req, db, nwordlist, None)
		jotools.write(req, '</table>\n<p>' +
		                   '<input type="hidden" name="confirm" value="on">' +
		                   '<input type="submit" value="%s"></p></form>\n' % _('Continue'))
		joheaders.page_footer_plain(req)
		return '\n'
	else:
		jotools.write(req, '<p>%s:</p>' % _('The following changes were made'))
		jotools.write(req,
		  '<table class="border"><tr><th>%s</th><th>%s</th><th>%s</th></tr>\n' \
		  % (_('Word'), _('Word class'), _('Notes')))
		_add_entry_fields(req, db, nwordlist, None)
		jotools.write(req, '</table>\n')
		jotools.write(req, '<p><a href="../">%s ...</a></p>\n' \
		                   % _('Back to main page'))
		joheaders.page_footer_plain(req)
		return '\n'

def categories(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, _('You are not allowed to edit data'))
		return '\n'
	db = jodb.connect()
	results = db.query("SELECT coalesce(info, ''), count(*) FROM raw_word " +
	                   "WHERE processed = FALSE " +
	                   "GROUP BY coalesce(info, '') " +
	                   "ORDER BY coalesce(info, '') ")
	if results.ntuples() == 0:
		joheaders.error_page(req, _('There are no words to be added'))
		return '\n'
	joheaders.page_header_navbar_level1(req, _("Add words"), uid, uname)
	jotools.write(req, "<p>%s:</p>\n" \
	                   % _('Choose a category from which you want to add words'))
	jotools.write(req, "<table><tr><th>%s</th><th>%s</th></tr>\n" \
	                   % (_('Category'), _('Words left')))
	for result in results.getresult():
		cat = str(result[0], 'UTF-8')
		if cat == '': cats = '(' + _('no category') + ')'
		else: cats = cat
		jotools.write(req, ('<tr><td><a href="add_from_db?category=%s">%s</a></td>' +
		                    '<td>%i</td></tr>\n') \
		  % (jotools.escape_url(result[0]), jotools.escape_html(cats), result[1]))
	jotools.write(req, "</table>\n")
	jotools.write(req, '<p><a href="add_from_db">%s ...</a></p>\n' % _('All words'))
	joheaders.page_footer_plain(req)
	return '\n'
