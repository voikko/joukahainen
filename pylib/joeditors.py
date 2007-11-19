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

# This file contains metadata display and editor components

import joindex
import jotools
import _config
import _apply_config

_ = _apply_config.translation.ugettext

def _word_class(db, classid):
	results = db.query("SELECT name FROM wordclass WHERE classid = %i" % classid)
	if results.ntuples() == 0:
		return _(u"Error: word class %i does not exist") % classid
	return (u"<span class=\"fheader\">%s:</span>" % _(u"Word class")) \
	      +(u" <span class=\"fsvalue\">%s</span>" % unicode(results.getresult()[0][0], 'UTF-8'))

def _flag_attributes(db, wid):
	results = db.query(("SELECT a.descr FROM attribute a, flag_attribute_value f " +
	                    "WHERE a.aid = f.aid AND a.type = 2 AND f.wid = %i") % wid)
	if results.ntuples() == 0: return u"<p>(%s)</p>" % _(u"No flags set")
	retdata = u"<ul>\n"
	for result in results.getresult():
		retdata = retdata + (u"<li>%s</li>\n" % unicode(result[0], 'UTF-8'))
	return retdata + u"</ul>\n"

def _string_attribute(db, wid, aid, editable):
	results = db.query(("SELECT s.value FROM string_attribute_value s " +
	                    "WHERE s.wid = %i AND s.aid = %i") % (wid, aid))
	if editable:
		if results.ntuples() == 0: oldval = u'""'
		else: oldval = jotools.escape_form_value(unicode(results.getresult()[0][0], 'UTF-8'))
		return u'<input type="text" value=%s size="60" name="string%i" id="string%i" />' \
		       % (oldval, aid, aid)
	else:
		if results.ntuples() == 0 : return u"(%s)" % _(u'Not set')
		return jotools.escape_html(unicode(results.getresult()[0][0], 'UTF-8'))

def _int_attribute(db, wid, aid, editable):
	results = db.query(("SELECT i.value FROM int_attribute_value i " +
	                    "WHERE i.wid = %i AND i.aid = %i") % (wid, aid))
	if editable:
		if results.ntuples() == 0: oldval = u''
		else: oldval = `results.getresult()[0][0]`
		return u'<input type="text" value="%s" size="10" name="int%i" />' % (oldval, aid)
	else:
		if results.ntuples() == 0 : return u"(%s)" % _(u'Not set')
		return `results.getresult()[0][0]`

def _related_words(db, wid):
	results = db.query("SELECT related_word FROM related_word WHERE wid = %i" % wid)
	if results.ntuples() == 0: return u"<p>(%s)</p>" % _(u'Not set')
	retdata = "<ul>\n"
	for result in results.getresult():
		retdata = retdata + ("<li>%s</li>\n" % unicode(result[0], 'UTF-8'))
	return retdata + "</ul>\n"

def _main_form_start(db, editable):
	if editable:
		return u'<form method="post" action="change" class="subform">'
	else:
		return u''

def _main_form_end(db, wid, editable):
	if editable:
		return u'''<p><span class="fheader">%s:</span>
<textarea name="comment" cols="80" rows="5"></textarea></p>
<p><input type="submit" value="%s" />
<input type="reset" value="%s" />
<input type="hidden" name="wid" value="%i" /></p>
</form>''' % (_(u'Add a comment'), _(u'Save changes'), _(u'Cancel changes'), wid)
	else:
		return u''

def _message_log(db, wid):
	retstr = u""
	results = db.query("SELECT u.uname, to_char(w.ctime, 'YYYY-MM-DD HH24:MI:SS'), " +
	                           "coalesce(u.firstname, ''), coalesce(u.lastname, '') " +
	                           "FROM word w, appuser u WHERE w.cuser = u.uid AND wid = %i" % wid)
	if results.ntuples() != 0:
		result = results.getresult()[0]
		date = result[1]
		user = jotools.escape_html(unicode(result[2], 'UTF-8')) + u" " + \
		       jotools.escape_html(unicode(result[3], 'UTF-8')) + u" (" + \
		       jotools.escape_html(unicode(result[0], 'UTF-8')) + u")"
		retstr = (u'<div class="logitem"><p class="date">%s %s</p>\n' % (user, date))
		retstr = retstr + u'<p class="logmsg">%s</p></div>\n' % _(u'Word created')
	results = db.query(("SELECT u.uname, to_char(e.etime, 'YYYY-MM-DD HH24:MI:SS'), e.message, " +
	                    "e.comment, coalesce(u.firstname, ''), coalesce(u.lastname, '') " +
	                    "FROM appuser u, event e " +
	                    "WHERE u.uid = e.euser AND e.eword = %i ORDER BY e.etime") % wid)
	for result in results.getresult():
		date = result[1]
		user = jotools.escape_html(unicode(result[4], 'UTF-8')) + u" " + \
		       jotools.escape_html(unicode(result[5], 'UTF-8')) + u" (" + \
		       jotools.escape_html(unicode(result[0], 'UTF-8')) + u")"
		retstr = retstr + (u'<div class="logitem"><p class="date">%s %s</p>\n' \
		                   % (user, date))
		if result[2] != None:
			msg = jotools.escape_html(unicode(result[2], 'UTF-8')).strip()
			msg = msg.replace(u'\n', u'<br />\n')
			retstr = retstr + u'<p class="logmsg">%s</p>\n' % msg
		if result[3] != None:
			comment = jotools.escape_html(unicode(result[3], 'UTF-8')).strip()
			comment = comment.replace(u'\n', u'<br />\n')
			comment = jotools.comment_links(comment)
			retstr = retstr + u'<p class="comment">%s</p>\n' % comment
		retstr = retstr + u"</div>\n"
	return retstr

def _flag_edit_form(db, wid, classid):
	results = db.query(("SELECT a.aid, a.descr, CASE WHEN fav.wid IS NULL THEN 'f' ELSE 't' END " +
	                    "FROM attribute_class ac, attribute a " +
	                    "LEFT OUTER JOIN flag_attribute_value fav ON (a.aid = fav.aid and fav.wid = %i) " +
	                    "WHERE a.aid = ac.aid AND ac.classid = %i AND a.type = 2" +
			"ORDER BY a.descr") % (wid, classid))
	if results.ntuples() == 0: return u"(%s)" % _(u'No flags available')
	retstr = u'<form method="post" action="flags"><p>\n'
	for result in results.getresult():
		retstr = retstr + u'<label><input type="checkbox" value="on" name="attr%i"' % result[0]
		if result[2] == 't': retstr = retstr + u' checked="checked"'
		retstr = retstr + u' />' + jotools.escape_html(unicode(result[1], 'UTF-8'))
		retstr = retstr + u'</label><br />\n'
	retstr = retstr + u'''<input type="hidden" name="wid" value="%i" /></p>
<p><span class="fheader">%s:</span>
<textarea name="comment" cols="80" rows="5"></textarea></p>
<p><input type="submit" value="%s" />
<input type="reset" value="%s" />
</p></form>''' % (wid, _(u'Add a comment'), _(u'Save changes'), _(u'Cancel changes'))
	return retstr

def _rwords_edit_form(db, wid):
	results = db.query(("SELECT r.rwid, r.related_word FROM related_word r " +
	                    "WHERE r.wid = %i ORDER BY r.related_word") % wid)
	retstr = u'<form method="post" action="rwords">\n'
	if results.ntuples() > 0:
		retstr = retstr + u'<h2>%s</h2>\n<p>\n' % _(u'Remove alternative forms')
	for result in results.getresult():
		retstr = retstr + u'<label><input type="checkbox" value="on" name="rword%i" />' % result[0]
		retstr = retstr + jotools.escape_html(unicode(result[1], 'UTF-8'))
		retstr = retstr + u'</label><br />\n'
	if results.ntuples() > 0:
		retstr = retstr + u'</p>\n'
	retstr = retstr + u'''<p><span class="fheader">%s</span>
<input type="text" size="80" name="add" /></p>
<p><span class="fheader">%s:</span>
<textarea name="comment" cols="80" rows="5"></textarea></p>
<p><input type="hidden" name="wid" value="%i" />
<input type="submit" value="%s" />
<input type="reset" value="%s" /></p>
</form>''' % (_(u'Add alternative forms'), _(u'Add a comment'), wid, _(u'Save changes'),
              _(u'Cancel changes'))
	return retstr

def _wiki_link(db, wikiattr, wid):
	results = db.query(("SELECT value FROM string_attribute_value WHERE " +
	                    "aid = %i and wid = %i") % (wikiattr, wid))
	if results.ntuples() == 0: return _(u'Word in Wiki')
	wikiurl = unicode(results.getresult()[0][0], 'UTF-8')
	if not wikiurl.startswith(u'http://'): return _(u'Word in Wiki')
	return u'<a href=%s>%s</a>' % (jotools.escape_form_value(wikiurl), _(u'Word in Wiki')) 

def call(db, funcname, paramlist):
	if funcname == 'word_class':
		if len(paramlist) != 1: return _(u"Error: 1 parameter expected")
		return _word_class(db, paramlist[0])
	if funcname == 'word_inflection':
		if len(paramlist) != 3: return _(u"Error: %i parameters expected" % 3)
		return _apply_config.joeditors_word_inflection(db, paramlist[0],
		                                               paramlist[1], paramlist[2])
	if funcname == 'kotus_class':
		if len(paramlist) != 2: return _(u"Error: %i parameters expected" % 2)
		return _apply_config.joeditors_kotus_class(db, paramlist[0], paramlist[1])
	if funcname == 'find_infclass':
		if len(paramlist) != 3: return _(u"Error: %i parameters expected" % 3)
		target = _apply_config.joeditors_find_infclass(db, paramlist[0], paramlist[1])
		if target == None: return u''
		return u'<a href="javascript:openInfclassFinder(\'%s\'+%s,\'string%s\')">%s</a>' \
		       % (_config.WWW_ROOT_DIR, target, paramlist[2], _(u'Find inflection class...'))
	if funcname == 'flag_attributes':
		if len(paramlist) != 1: return _(u"Error: 1 parameter expected")
		return _flag_attributes(db, paramlist[0])
	if funcname == 'string_attribute':
		if len(paramlist) != 3: return _(u"Error: %i parameters expected" % 3)
		return _string_attribute(db, paramlist[0], paramlist[1], paramlist[2])
	if funcname == 'int_attribute':
		if len(paramlist) != 3: return _(u"Error: %i parameters expected" % 3)
		return _int_attribute(db, paramlist[0], paramlist[1], paramlist[2])
	if funcname == 'related_words':
		if len(paramlist) != 1: return _(u"Error: 1 parameter expected")
		return _related_words(db, paramlist[0])
	if funcname == 'login_logout':
		if len(paramlist) != 3: return _(u"Error: %i parameters expected" % 3)
		return joindex.login_logout(db, paramlist[0], paramlist[1], paramlist[2])
	if funcname == 'main_form_start':
		if len(paramlist) != 1: return _(u"Error: 1 parameter expected")
		return _main_form_start(db, paramlist[0])
	if funcname == 'main_form_end':
		if len(paramlist) != 2: return _(u"Error: %i parameters expected" % 2)
		return _main_form_end(db, paramlist[0], paramlist[1])
	if funcname == 'message_log':
		if len(paramlist) != 1: return _(u"Error: 1 parameter expected")
		return _message_log(db, paramlist[0])
	if funcname == 'flag_edit_form':
		if len(paramlist) != 2: return _(u"Error: %i parameters expected" % 2)
		return _flag_edit_form(db, paramlist[0], paramlist[1])
	if funcname == 'rwords_edit_form':
		if len(paramlist) != 1: return _(u"Error: 1 parameter expected")
		return _rwords_edit_form(db, paramlist[0])
	if funcname == 'wiki_link':
		if len(paramlist) != 2: return _(u"Error: %i parameters expected" % 2)
		return _wiki_link(db, paramlist[0], paramlist[1])
	return _(u"Error: unknown function")
