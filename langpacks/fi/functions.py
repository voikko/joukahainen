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

# This file contains language specific program code for Finnish

import os

# Path to module directory (Hunspell-fi tools)
MODULE_PATH_HFTOOLS = '/home/harri/hunspell-fi/svn/trunk/tools/pylib'

# Path to Hunspell-fi data directory
HF_DATA = '/home/harri/hunspell-fi/svn/trunk/data'
VOIKKO_DATA = "/home/harri/svn/voikko/trunk/data"

import sys
sys.path.append(MODULE_PATH_HFTOOLS)
import hfaffix
import hfutils
import hfconv
import voikkoutils
import xml.sax.saxutils
import time

# Returns the vowel type for a word in the database.
def _get_db_vowel_type(db, wid):
	results = db.query(("SELECT aid FROM flag_attribute_value " +
	                    "WHERE wid = %i AND aid IN (22, 23)") % wid)
	if results.ntuples() == 0: return hfutils.VOWEL_DEFAULT
	elif results.ntuples() == 1:
		if results.getresult()[0][0] == 22: return hfutils.VOWEL_FRONT
		else: return hfutils.VOWEL_BACK
	else: return hfutils.VOWEL_BOTH


# Returns autodetected vowel type of infection suffixes for a simple word.
# If word contains character '=', automatic detection is only performed on the
# trailing part. If word contains character '|', automatic detection is performed
# on the trailing part and the whole word, and the union of accepted vowel types is returned.
def _get_wordform_infl_vowel_type(wordform):
	# Search for last '=' or '-', check the trailing part using recursion
	startind = max(wordform.rfind(u'='), wordform.rfind(u'-'))
	if startind == len(wordform) - 1: return hfutils.VOWEL_BOTH # Not allowed
	if startind != -1: return _get_wordform_infl_vowel_type(wordform[startind+1:])
	
	# Search for first '|', check the trailing part using recursion
	startind = wordform.find(u'|')
	if startind == len(wordform) - 1: return hfutils.VOWEL_BOTH # Not allowed
	vtype_whole = hfutils.vowel_type(wordform)
	if startind == -1: return vtype_whole
	vtype_part = _get_wordform_infl_vowel_type(wordform[startind+1:])
	if vtype_whole == vtype_part: return vtype_whole
	else: return hfutils.VOWEL_BOTH


# Returns the vowel type of inflection suffixes for a word in the database.
def _get_infl_vowel_type(db, wid, word):
	# Check the database
	dbtype = _get_db_vowel_type(db, wid)
	if dbtype != hfutils.VOWEL_DEFAULT: return dbtype
	# Check alternative spellings
	altforms_res = db.query('SELECT related_word FROM related_word WHERE wid = %i' % wid)
	for altform_r in altforms_res.getresult():
		altform = unicode(altform_r[0], 'UTF-8')
		if altform.replace(u'|', u'').replace(u'=', u'') == word:
			return _get_wordform_infl_vowel_type(altform)
	# Return the default
	return _get_wordform_infl_vowel_type(word)


WCHARS = u"abcdefghijklmnopqrstuvwxyzåäöszèéšžáóABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖŠŽÈÉŠŽ-'|="
# Checks if string looks like a valid word. This is a mandatory function.
def checkword(string):
	for c in string:
		if not c in WCHARS: return False
	return True


SINGULAR_FORMS = ['nominatiivi', 'genetiivi', 'partitiivi', 'translatiivi', 'essiivi',
                  'inessiivi', 'elatiivi', 'illatiivi', 'adessiivi', 'ablatiivi',
	        'allatiivi', 'abessiivi']
CHARACTERISTIC_NOUN_FORMS = ['nominatiivi', 'genetiivi', 'partitiivi', 'illatiivi',
                             'genetiivi_mon', 'partitiivi_mon', 'illatiivi_mon']
CHARACTERISTIC_VERB_FORMS = ['infinitiivi_1', 'preesens_yks_1', 'imperfekti_yks_3',
                             'kondit_yks_3', 'imperatiivi_yks_3', 'partisiippi_2',
                             'imperfekti_pass']

# Returns the inflection class and gradation class for a word in Joukahainen
# Returns tuple (inflclass_main, grad_type) or None, if no inflection was available
def _get_inflection_gradation(db, wid):
	results = db.query(("SELECT value FROM string_attribute_value " +
	                    "WHERE wid = %i AND aid = 1") % wid)
	if results.ntuples() != 1: return None
	result = results.getresult()[0]
	infclass_parts = unicode(result[0], 'UTF-8').split('-')
	if len(infclass_parts) == 1:
		infclass_main = unicode(result[0], 'UTF-8')
		grad_type = '-'
	elif len(infclass_parts) == 2:
		infclass_main = infclass_parts[0]
		grad_type = infclass_parts[1]
	else: return None
	return (infclass_main, grad_type)


# Returns the correct hfutils class structure for given word.
# classid is the word class identifier in Joukahainen.
# Returns None if no class information could be retrieved
def _get_hfutils_class(wid, classid, infclass_main):
	if classid in [1, 2]: classdatafile = HF_DATA + "/subst.aff"
	elif classid == 3: classdatafile = HF_DATA + "/verb.aff"
	else: return None
	
	word_classes = hfaffix.read_word_classes(classdatafile)
	for word_class in word_classes:
		if not infclass_main in word_class['smcnames']: continue
		else: return word_class
	return None


# Inflection table for a Finnish noun or verb.
def word_inflection(db, wid, word, classid):
	if classid in [1, 2]: characteristic_forms = CHARACTERISTIC_NOUN_FORMS
	elif classid == 3: characteristic_forms = CHARACTERISTIC_VERB_FORMS
	else: return "(ei taivutuksia tämän sanaluokan sanoille)"
	
	infclass_parts = _get_inflection_gradation(db, wid)
	if infclass_parts == None: return u"(ei taivutusluokkaa)"
	(infclass_main, grad_type) = infclass_parts
	
	word_class = _get_hfutils_class(wid, classid, infclass_main)
	if word_class == None: return "(taivutuksia ei ole saatavilla tai virheellinen taivutusluokka)"
	
	tableid = u"inftable%i" % wid
	retdata = u''
	note = u''
	have_only_characteristic = True
	inflected_words = hfaffix.inflect_word(word, grad_type, word_class,
	                                       _get_infl_vowel_type(db, wid, word))
	if inflected_words == None: return "(virhe taivutusten muodostuksessa)"
	
	if classid in [1, 2] and \
	   db.query("SELECT count(*) FROM flag_attribute_value WHERE aid = 37 AND wid = %i" \
	   % wid).getresult()[0][0] == 1: no_singular = True
	else: no_singular = False
	
	form = None
	inflist = []
	inflected_words.append((u'', u'', u''))
	for inflected_word in inflected_words:
		if no_singular and inflected_word[0] in SINGULAR_FORMS: continue
		if form != inflected_word[0]:
			if form != None and len(inflist) > 0:
				if form in characteristic_forms:
					htmlclass = u' class="characteristic"'
				elif form[0] == u'!':
					htmlclass = u' class="characteristic"'
					form = form[1:]
				else:
					htmlclass = ''
					have_only_characteristic = False
				infs = reduce(lambda x, y: u"%s, %s" % (x, y), inflist)
				retdata = retdata + (u"<tr%s><td>%s</td><td>%s</td></tr>\n" %
				          (htmlclass, form, infs))
			inflist = []
			form = inflected_word[0]
		if hfutils.read_option(inflected_word[2], 'ps', '-') != 'r' \
		   and not inflected_word[1] in inflist:
			inflist.append(inflected_word[1])
	note = word_class['note']
	
	table_header = u'<table class="inflection" id="%s">\n<tr><th colspan="2">' % tableid
	if not have_only_characteristic:
		table_header = table_header \
		               + u'<a href="javascript:switchDetailedDisplay(\'%s\');" id="%s"></a>' \
			     % (tableid, tableid + u'a')
	table_header = table_header + u'Taivutus</th></tr>\n'
	if note == u'': notetext = u''
	else: notetext = u'<p>%s</p>\n' % note
	return notetext + table_header + retdata + u'</table>\n'

# Returns tuple (alku, jatko) for given word in Joukahainen
def _find_malaga_word_class(word, hf_class, hf_histclass, hf_wordclass):
	# If historical class was set, see first if it can be used in Malaga
	for histclass in hfconv.histmap:
		if hf_histclass == histclass[0]:
			for infclass in hfconv.classmap:
				for subclass in infclass[2]:
					if subclass[2] == histclass[1]:
						alku = hfconv.match_re(word, subclass[1])
						if alku != None: return (alku, hf_histclass)
	
	# No (usable) historical class, use the modern class
	classparts = hf_class.split(u'-')
	if len(classparts) == 1:
		classparts.append(None)
		gradtypes = [ None ]
	else:
		gradtypes = []
		for grad in hfconv.grads:
			if grad[2] == classparts[1]: gradtypes.append(grad[1])
	
	for infclass in hfconv.classmap:
		if infclass[0] != classparts[0]: continue
		for subclass in infclass[2]:
			if len(subclass) > 3 and not hf_wordclass in subclass[3]: continue
			if not subclass[0] in gradtypes: continue
			alku = hfconv.match_re(word, subclass[1])
			if alku != None: return (alku, subclass[2])
	
	return (None, None)

# Returns tuple (luokka, tiedot) for given word in Joukahainen
def _get_class_and_flags(db, hf_wclass, wid):
	flags = db.query('SELECT aid FROM flag_attribute_value WHERE wid = %i' % wid)
	flag_s = u''
	if hf_wclass == 1: class_s = u'nimisana'
	elif hf_wclass == 2: class_s = u'laatusana'
	elif hf_wclass == 3: class_s = u'teonsana'
	for flag in flags.getresult():
		if hf_wclass == 2 and flag[0] == 10: class_s = u'nimi_laatusana'
		elif hf_wclass == 1 and flag[0] == 11: class_s = u'etunimi'
		elif hf_wclass == 1 and flag[0] == 12: class_s = u'sukunimi'
		elif hf_wclass == 1 and flag[0] == 13: class_s = u'paikannimi'
		elif hf_wclass == 1 and flag[0] == 14: class_s = u'nimi'
		else:
			for f in hfconv.flagmap:
				if flag[0] == f[1]: flag_s = flag_s + f[0] + u', '
	if flag_s == u'': flag_s = None
	else: flag_s = flag_s[:-2]
	return (class_s, flag_s)

# Returns a string describing the structure of a word, if necessary for the spellchecker
# or hyphenator
def _get_structure(wordform, malaga_class_s):
	needstructure = False
	if malaga_class_s in [u'nimi', u'etunimi', u'sukunimi', 'paikannimi']: ispropernoun = True
	else: ispropernoun = False
	structstr = u', rakenne: "='
	for i in range(len(wordform)):
		c = wordform[i]
		if c == u'-':
			structstr = structstr + u"-="
			needstructure = True
		elif c == u'|': structstr = structstr
		elif c == u'=':
			structstr = structstr + u"="
			needstructure = True
		elif c == u':':
			structstr = structstr + u":"
			needstructure = True
		elif c.isupper():
			structstr = structstr + u"i"
			if not (ispropernoun and i == 0): needstructure = True
		else: structstr = structstr + u"p"
	if needstructure: return structstr + u'"'
	else: return u""

# Prints a line or lines to be added to Suomi-malaga lexicon for given word
def _malaga_line(db, req, wid, word, classid, hf_class, hf_histclass):
	altforms_res = db.query('SELECT related_word FROM related_word WHERE wid = %i' % wid)
	if altforms_res.ntuples() == 0: altforms = [word]
	else:
		altforms = []
		for res in altforms_res.getresult():
			altforms.append(unicode(res[0], 'UTF-8'))
	forced_vtype = _get_db_vowel_type(db, wid)
	for altform in altforms:
		word = altform.replace(u'|', u'').replace(u'=', u'')
		if classid in [1, 2, 3]:
			(alku, jatko) = _find_malaga_word_class(word, hf_class, hf_histclass, classid)
			if alku == None:
				req.write((u"#Malaga class not found for (%s, %i, %s)\n" \
				              % (word, classid, hf_class)).encode('UTF-8'))
				continue
			if forced_vtype == hfutils.VOWEL_DEFAULT:
				vtype = _get_wordform_infl_vowel_type(altform)
			else: vtype = forced_vtype
			if vtype == hfutils.VOWEL_FRONT: malaga_vtype = u'ä'
			elif vtype == hfutils.VOWEL_BACK: malaga_vtype = u'a'
			elif vtype == hfutils.VOWEL_BOTH: malaga_vtype = u'aä'
			(wclass_s, flags) = _get_class_and_flags(db, classid, wid)
			if flags == None: flags = u''
			else: flags = u', tiedot: <%s>' % flags
			req.write((u'[perusmuoto: "%s", alku: "%s", luokka: %s, jatko: <%s>, äs: %s%s%s];\n' \
			          % (word, alku, wclass_s, jatko, malaga_vtype, flags,
				   _get_structure(altform, wclass_s))).encode('UTF-8'))

def _jooutput_malaga(req, db, query):
	req.content_type = "text/plain"
	req.send_http_header()
	req.write((u"""# This file is generated for use in Suomi-malaga by
# vocabulary management application Joukahainen.
# This data is based on Suomi-malaga 0.7 by Hannu Väisänen, and includes
# modifications from people listed in file CONTRIBUTORS of current Suomi-malaga
# Voikko edition Subversion repository (or, if you have received this file as a
# part of Suomi-malaga, the file is located at the root directory of the source
# package). For more information, see http://joukahainen.lokalisointi.org
#
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
#
# Time of generation: %s

""" % time.strftime("%Y-%m-%d %H:%M:%S %Z")).encode('UTF-8'))
	results = db.query(("SELECT w.word, w.class, sa.value, w.wid, hc.value, fc.value, cf.aid " +
	"FROM string_attribute_value sa, " +
	"(%s) w LEFT JOIN string_attribute_value hc ON (w.wid = hc.wid AND hc.aid = 16) " +
	"LEFT JOIN int_attribute_value fc ON (w.wid = fc.wid AND fc.aid = 38) " +
	"LEFT JOIN flag_attribute_value cf ON (w.wid = cf.wid AND cf.aid = 39) " +
	"WHERE w.wid = sa.wid AND sa.aid = 1 AND sa.value != 'poikkeava' " +
	"ORDER BY w.word, w.class, w.wid") % query)
	for result in results.getresult():
		# drop too rare words
		if result[5] > 9 or (result[5] == 9 and result[6] == 39): continue
		wid = result[3]
		word = unicode(result[0], 'UTF-8')
		classid = result[1]
		if result[2] == None: continue
		hf_class = unicode(result[2], 'UTF-8')
		if result[4] == None: hf_histclass = None
		else: hf_histclass = unicode(result[4], 'UTF-8')
		_malaga_line(db, req, wid, word, classid, hf_class, hf_histclass)


def _get_xml_flags(flags, flagtype, flaglist):
	results = []
	for flag in flaglist:
		if flag.xmlGroup == flagtype and flag.joukahainen in flags:
			results.append(u'<flag>%s</flag>' % flag.xmlFlag)
	return results

def _write_xml_forms(db, req, wid, word):
	altforms_res = db.query('SELECT related_word FROM related_word ' \
	                        + 'WHERE wid = %i ORDER BY related_word' % wid)
	altforms = [word]
	for res in altforms_res.getresult():
		altform = unicode(res[0], 'UTF-8')
		if altform != word:	altforms.append(altform)
	req.write('\t<forms>\n')
	for form in altforms:
		req.write((u'\t\t<form>%s</form>\n' % form).encode('UTF-8'))
	req.write('\t</forms>\n')

def _write_xml_classes(req, wid, classid, flags):
	req.write('\t<classes>\n')
	if classid == 1:
		if len(set(flags) & set([11, 12, 13, 14])) > 0:
			if 11 in flags: req.write('\t\t<class>pnoun_firstname</class>\n')
			if 12 in flags: req.write('\t\t<class>pnoun_lastname</class>\n')
			if 13 in flags: req.write('\t\t<class>pnoun_place</class>\n')
			if 14 in flags: req.write('\t\t<class>pnoun_misc</class>\n')
		else: req.write(u'\t\t<class>noun</class>\n')
	elif classid == 2:
		if 10 in flags: req.write(u'\t\t<class>noun</class>\n')
		req.write(u'\t\t<class>adjective</class>\n')
	elif classid == 3: req.write(u'\t\t<class>verb</class>\n')
	req.write('\t</classes>\n')

def _write_xml_inflection(req, flags, strings, flaglist):
	elements = []
	
	for s in strings:
		if s[0] == 1: elements.append(u'<infclass>%s</infclass>' % s[1])
		if s[0] == 16: elements.append(u'<infclass type="historical">%s</infclass>' % s[1])
	
	if 22 in flags:
		if 23 in flags: elements.append(u'<vtype>aä</vtype>')
		else: elements.append(u'<vtype>ä</vtype>')
	elif 23 in flags: elements.append(u'<vtype>a</vtype>')
	
	for f in _get_xml_flags(flags, 'inflection', flaglist): elements.append(f)
	
	if len(elements) > 0:
		req.write('\t<inflection>\n')
		for element in elements:
			req.write('\t\t%s\n' % element.encode('UTF-8'))
		req.write('\t</inflection>\n')

def _write_xml_flagset(req, flags, flaglist, flagname):
	elements = _get_xml_flags(flags, flagname, flaglist)
	if len(elements) > 0:
		req.write('\t<%s>\n' % flagname)
		for element in elements:
			req.write('\t\t%s\n' % element.encode('UTF-8'))
		req.write('\t</%s>\n' % flagname)

def _write_xml_frequency(req, flags, integers, flaglist):
	elements = []
	
	for i in integers:
		if i[0] == 38: elements.append(u'<fclass>%i</fclass>' % i[1])
	
	for f in _get_xml_flags(flags, 'frequency', flaglist): elements.append(f)
	
	if len(elements) > 0:
		req.write('\t<frequency>\n')
		for element in elements:
			req.write('\t\t%s\n' % element.encode('UTF-8'))
		req.write('\t</frequency>\n')

def _write_xml_info(req, strings):
	elements = []
	
	for s in strings:
		if s[0] == 18:
			elements.append(u'<description>%s</description>' \
			                % xml.sax.saxutils.escape(s[1]))
		if s[0] == 28:
			elements.append(u'<link>%s</link>' \
			                % xml.sax.saxutils.escape(s[1]))
	
	if len(elements) > 0:
		req.write('\t<info>\n')
		for element in elements:
			req.write('\t\t%s\n' % element.encode('UTF-8'))
		req.write('\t</info>\n')

def _write_xml_word(db, req, wid, flaglist):
	req.write('<word id="w%i">\n' % wid)
	
	# Information from table word
	results = db.query("SELECT w.word, w.class FROM word w WHERE w.wid = %i" % wid).getresult()
	if len(results) == 0: return
	result = results[0]
	word = unicode(result[0], 'UTF-8')
	classid = result[1]
	
	# Information from table flag_attribute_value
	results = db.query("SELECT aid FROM flag_attribute_value " \
	                   + "WHERE wid = %i ORDER BY aid" % wid).getresult()
	flags = []
	for r in results: flags.append(r[0])
	
	# Information from table string_attribute_value
	results = db.query("SELECT aid, value FROM string_attribute_value " \
	                   + "WHERE wid = %i ORDER BY aid" % wid).getresult()
	strings = []
	for s in results: strings.append((s[0], unicode(s[1], 'UTF-8')))
	
	# Information from table int_attribute_value
	integers = db.query("SELECT aid, value FROM int_attribute_value " \
	                    + "WHERE wid = %i ORDER BY aid" % wid).getresult()
	
	_write_xml_forms(db, req, wid, word)
	_write_xml_classes(req, wid, classid, flags)
	_write_xml_inflection(req, flags, strings, flaglist)
	_write_xml_flagset(req, flags, flaglist, 'usage')
	_write_xml_flagset(req, flags, flaglist, 'compounding')
	_write_xml_flagset(req, flags, flaglist, 'derivation')
	_write_xml_flagset(req, flags, flaglist, 'style')
	_write_xml_flagset(req, flags, flaglist, 'application')
	_write_xml_frequency(req, flags, integers, flaglist)
	_write_xml_info(req, strings)
	
	req.write('</word>\n')

def _jooutput_xml(req, db, query):
	req.content_type = "application/xml"
	req.send_http_header()
	req.write((u'''<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE wordlist SYSTEM "wordlist.dtd">
<!--
  This file is generated by vocabulary management application Joukahainen.
  It contains entries from the vocabulary database of the Voikko project.
  The copyright holders are listed in file CONTRIBUTORS of current Suomi-malaga
  Voikko edition Subversion repository (or, if you have received this file as a
  part of Suomi-malaga, the file is located at the root directory of the source
  package). For more information, see http://joukahainen.lokalisointi.org

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

  Time of generation: %s
-->
<wordlist xml:lang="fi">
''' % time.strftime("%Y-%m-%d %H:%M:%S %Z")).encode('UTF-8'))
	
	flaglist = voikkoutils.readFlagAttributes(VOIKKO_DATA + "/words/flags.txt")
	
	results = db.query(("SELECT w.wid FROM (%s) w " +
	"WHERE w.wid NOT IN (SELECT f.wid FROM flag_attribute_value f " +
	" WHERE f.aid IN (24, 26)) " +
	"ORDER BY w.wid") % query)
	for result in results.getresult():
		_write_xml_word(db, req, result[0], flaglist)
	
	req.write("</wordlist>\n")


# Lists the language specific output types. This is a mandatory function
def jooutput_list_supported_types():
	types = []
	types.append(('malaga', u'Tulosta Suomi-malagan käyttämässä muodossa'))
	types.append(('xml', u'Tulosta XML-muodossa'))
	return types

# Language specific list output. This is a mandatory function
def jooutput_call(req, outputtype, db, query):
	if outputtype == 'malaga':
		_jooutput_malaga(req, db, query)
	elif outputtype == 'xml':
		_jooutput_xml(req, db, query)
	else:
		joheaders.error_page(req, _(u'Unsupported output type'))

# Returns information about the classification of the word in the format used by
# the Research Institute for the Languages of Finland
def kotus_class(db, wid, classid):
	infclass_parts = _get_inflection_gradation(db, wid)
	if infclass_parts == None: return u""
	(infclass_main, grad_type) = infclass_parts
	
	word_class = _get_hfutils_class(wid, classid, infclass_main)
	if word_class == None: return ""
	
	return u'<span class="fheader">Kotus-luokka:</span> <span class="fsvalue">%s</span>' \
	       % word_class['cname']

# Returns a link target of the inflection class finder for a word or None,
# if no finder is available
def find_infclass(db, word, classid):
	if classid in [1, 2]: finderclass = 1
	elif classid == 3: finderclass = 3
	else: return None
	return u'/findclass/classlist?word=%s&class=%i' % (word, finderclass)
