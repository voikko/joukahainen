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

# This file contains metadata display and editor components

import joindex
import jotools
import functions
import _config
import gettext

_ = gettext.gettext

def _word_class(db, classid):
	results = db.query("SELECT name FROM wordclass WHERE classid = %i" % classid)
	if results.ntuples() == 0:
		return _("Error: word class %i does not exist") % classid
	return ("<span class=\"fheader\">%s:</span>" % _("Word class")) \
	      +(" <span class=\"fsvalue\">%s</span>" % results.getresult()[0][0])

def _flag_attributes(db, wid):
	results = db.query(("SELECT a.descr FROM attribute a, flag_attribute_value f " +
	                    "WHERE a.aid = f.aid AND a.type = 2 AND f.wid = %i ORDER BY a.descr") % wid)
	if results.ntuples() == 0: return "<p>(%s)</p>" % _("No flags set")
	retdata = "<ul>\n"
	for result in results.getresult():
		retdata = retdata + ("<li>%s</li>\n" % result[0])
	return retdata + "</ul>\n"

def _string_attribute(db, wid, aid, editable):
	results = db.query(("SELECT s.value FROM string_attribute_value s " +
	                    "WHERE s.wid = %i AND s.aid = %i") % (wid, aid))
	if editable:
		if results.ntuples() == 0: oldval = '""'
		else: oldval = jotools.escape_form_value(results.getresult()[0][0])
		return '<input type="text" value=%s size="60" name="string%i" id="string%i" />' \
		       % (oldval, aid, aid)
	else:
		if results.ntuples() == 0 : return "(%s)" % _('Not set')
		return jotools.escape_html(results.getresult()[0][0])

def _int_attribute(db, wid, aid, editable):
	results = db.query(("SELECT i.value FROM int_attribute_value i " +
	                    "WHERE i.wid = %i AND i.aid = %i") % (wid, aid))
	if editable:
		if results.ntuples() == 0: oldval = ''
		else: oldval = repr(results.getresult()[0][0])
		return '<input type="text" value="%s" size="10" name="int%i" />' % (oldval, aid)
	else:
		if results.ntuples() == 0 : return "(%s)" % _('Not set')
		return repr(results.getresult()[0][0])

def _related_words(db, wid):
	results = db.query("SELECT related_word FROM related_word WHERE wid = %i ORDER BY related_word" % wid)
	if results.ntuples() == 0: return "<p>(%s)</p>" % _('Not set')
	retdata = "<ul>\n"
	for result in results.getresult():
		retdata = retdata + ("<li>%s</li>\n" % result[0])
	return retdata + "</ul>\n"

def _main_form_start(db, editable):
	if editable:
		return '<form method="post" action="change" class="subform">'
	else:
		return ''

def _main_form_end(db, wid, editable):
	if editable:
		return '''<p><span class="fheader">%s:</span>
<textarea name="comment" cols="80" rows="5"></textarea></p>
<p><input type="submit" value="%s" />
<input type="reset" value="%s" />
<input type="hidden" name="wid" value="%i" /></p>
</form>''' % (_('Add a comment'), _('Save changes'), _('Cancel changes'), wid)
	else:
		return ''

def _message_log(db, wid):
	retstr = ""
	results = db.query("SELECT u.uname, to_char(w.ctime, 'YYYY-MM-DD HH24:MI:SS'), " +
	                           "coalesce(u.firstname, ''), coalesce(u.lastname, '') " +
	                           "FROM word w, appuser u WHERE w.cuser = u.uid AND wid = %i" % wid)
	if results.ntuples() != 0:
		result = results.getresult()[0]
		date = result[1]
		user = jotools.escape_html(result[2]) + " " + \
		       jotools.escape_html(result[3]) + " (" + \
		       jotools.escape_html(result[0]) + ")"
		retstr = ('<div class="logitem"><p class="date">%s %s</p>\n' % (user, date))
		retstr = retstr + '<p class="logmsg">%s</p></div>\n' % _('Word created')
	results = db.query(("SELECT u.uname, to_char(e.etime, 'YYYY-MM-DD HH24:MI:SS'), e.message, " +
	                    "e.comment, coalesce(u.firstname, ''), coalesce(u.lastname, '') " +
	                    "FROM appuser u, event e " +
	                    "WHERE u.uid = e.euser AND e.eword = %i ORDER BY e.etime") % wid)
	for result in results.getresult():
		date = result[1]
		user = jotools.escape_html(result[4]) + " " + \
		       jotools.escape_html(result[5]) + " (" + \
		       jotools.escape_html(result[0]) + ")"
		retstr = retstr + ('<div class="logitem"><p class="date">%s %s</p>\n' \
		                   % (user, date))
		if result[2] != None:
			msg = jotools.escape_html(result[2]).strip()
			msg = msg.replace('\n', '<br />\n')
			retstr = retstr + '<p class="logmsg">%s</p>\n' % msg
		if result[3] != None:
			comment = jotools.escape_html(result[3]).strip()
			comment = comment.replace('\n', '<br />\n')
			comment = jotools.comment_links(comment)
			retstr = retstr + '<p class="comment">%s</p>\n' % comment
		retstr = retstr + "</div>\n"
	return retstr

def _flag_edit_form(db, wid, classid):
	results = db.query(("SELECT a.aid, a.descr, CASE WHEN fav.wid IS NULL THEN 'f' ELSE 't' END " +
	                    "FROM attribute_class ac, attribute a " +
	                    "LEFT OUTER JOIN flag_attribute_value fav ON (a.aid = fav.aid and fav.wid = %i) " +
	                    "WHERE a.aid = ac.aid AND ac.classid = %i AND a.type = 2" +
			"ORDER BY a.descr") % (wid, classid))
	if results.ntuples() == 0: return "(%s)" % _('No flags available')
	retstr = '<form method="post" action="flags"><p>\n'
	for result in results.getresult():
		retstr = retstr + '<label><input type="checkbox" value="on" name="attr%i"' % result[0]
		if result[2] == 't': retstr = retstr + ' checked="checked"'
		retstr = retstr + ' />' + jotools.escape_html(str(result[1], 'UTF-8'))
		retstr = retstr + '</label><br />\n'
	retstr = retstr + '''<input type="hidden" name="wid" value="%i" /></p>
<p><span class="fheader">%s:</span>
<textarea name="comment" cols="80" rows="5"></textarea></p>
<p><input type="submit" value="%s" />
<input type="reset" value="%s" />
</p></form>''' % (wid, _('Add a comment'), _('Save changes'), _('Cancel changes'))
	return retstr

def _rwords_edit_form(db, wid):
	results = db.query(("SELECT r.rwid, r.related_word FROM related_word r " +
	                    "WHERE r.wid = %i ORDER BY r.related_word") % wid)
	retstr = '<form method="post" action="rwords">\n'
	if results.ntuples() > 0:
		retstr = retstr + '<h2>%s</h2>\n<p>\n' % _('Remove alternative forms')
	for result in results.getresult():
		retstr = retstr + '<label><input type="checkbox" value="on" name="rword%i" />' % result[0]
		retstr = retstr + jotools.escape_html(str(result[1], 'UTF-8'))
		retstr = retstr + '</label><br />\n'
	if results.ntuples() > 0:
		retstr = retstr + '</p>\n'
	retstr = retstr + '''<p><span class="fheader">%s</span>
<input type="text" size="80" name="add" /></p>
<p><span class="fheader">%s:</span>
<textarea name="comment" cols="80" rows="5"></textarea></p>
<p><input type="hidden" name="wid" value="%i" />
<input type="submit" value="%s" />
<input type="reset" value="%s" /></p>
</form>''' % (_('Add alternative forms'), _('Add a comment'), wid, _('Save changes'),
              _('Cancel changes'))
	return retstr

def _wiki_link(db, wikiattr, wid):
	results = db.query(("SELECT value FROM string_attribute_value WHERE " +
	                    "aid = %i and wid = %i") % (wikiattr, wid))
	if results.ntuples() == 0: return _('Word in Wiki')
	wikiurl = str(results.getresult()[0][0], 'UTF-8')
	if not wikiurl.startswith('http://') and not wikiurl.startswith('https://'):
		return _('Word in Wiki')
	return '<a href=%s>%s</a>' % (jotools.escape_form_value(wikiurl), _('Word in Wiki')) 

def call(db, funcname, paramlist):
	if funcname == 'word_class':
		if len(paramlist) != 1: return _("Error: 1 parameter expected")
		return _word_class(db, paramlist[0])
	if funcname == 'word_inflection':
		if len(paramlist) != 3: return _("Error: %i parameters expected" % 3)
		return functions.word_inflection(db, paramlist[0],
		                                               paramlist[1], paramlist[2])
	if funcname == 'kotus_class':
		if len(paramlist) != 3: return _("Error: %i parameters expected" % 3)
		return functions.kotus_class(db, paramlist[0], paramlist[1],
		                                           paramlist[2])
	if funcname == 'find_infclass':
		if len(paramlist) != 3: return _("Error: %i parameters expected" % 3)
		target = functions.find_infclass(db, paramlist[0], paramlist[1])
		if target == None: return ''
		return '<a href="javascript:openInfclassFinder(\'%s\'+%s,\'string%s\')">%s</a>' \
		       % (_config.WWW_ROOT_DIR, target, paramlist[2], _('Find inflection class...'))
	if funcname == 'flag_attributes':
		if len(paramlist) != 1: return _("Error: 1 parameter expected")
		return _flag_attributes(db, paramlist[0])
	if funcname == 'string_attribute':
		if len(paramlist) != 3: return _("Error: %i parameters expected" % 3)
		return _string_attribute(db, paramlist[0], paramlist[1], paramlist[2])
	if funcname == 'int_attribute':
		if len(paramlist) != 3: return _("Error: %i parameters expected" % 3)
		return _int_attribute(db, paramlist[0], paramlist[1], paramlist[2])
	if funcname == 'related_words':
		if len(paramlist) != 1: return _("Error: 1 parameter expected")
		return _related_words(db, paramlist[0])
	if funcname == 'login_logout':
		if len(paramlist) != 3: return _("Error: %i parameters expected" % 3)
		return joindex.login_logout(db, paramlist[0], paramlist[1], paramlist[2])
	if funcname == 'main_form_start':
		if len(paramlist) != 1: return _("Error: 1 parameter expected")
		return _main_form_start(db, paramlist[0])
	if funcname == 'main_form_end':
		if len(paramlist) != 2: return _("Error: %i parameters expected" % 2)
		return _main_form_end(db, paramlist[0], paramlist[1])
	if funcname == 'message_log':
		if len(paramlist) != 1: return _("Error: 1 parameter expected")
		return _message_log(db, paramlist[0])
	if funcname == 'flag_edit_form':
		if len(paramlist) != 2: return _("Error: %i parameters expected" % 2)
		return _flag_edit_form(db, paramlist[0], paramlist[1])
	if funcname == 'rwords_edit_form':
		if len(paramlist) != 1: return _("Error: 1 parameter expected")
		return _rwords_edit_form(db, paramlist[0])
	if funcname == 'wiki_link':
		if len(paramlist) != 2: return _("Error: %i parameters expected" % 2)
		return _wiki_link(db, paramlist[0], paramlist[1])
	return _("Error: unknown function")
