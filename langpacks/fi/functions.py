# -*- coding: utf-8 -*-

# Copyright 2006 - 2008 Harri Pitkänen (hatapitk@iki.fi)
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

# This file contains language specific program code for Finnish

import sys
import voikkoutils
import voikkoinfl
import xml.sax.saxutils
import time

# Path to Voikko data directory
VOIKKO_DATA = voikkoutils.get_preference('voikko_data_dir')

# Cached inflection rules
_NOUN_INFLECTIONS = None
_VERB_INFLECTIONS = None
def _ensure_infdata_available():
	global _NOUN_INFLECTIONS
	global _VERB_INFLECTIONS
	if _NOUN_INFLECTIONS == None:
		_NOUN_INFLECTIONS = voikkoinfl.readInflectionTypes(VOIKKO_DATA + "/subst.aff")
	if _VERB_INFLECTIONS == None:
		_VERB_INFLECTIONS = voikkoinfl.readInflectionTypes(VOIKKO_DATA + "/verb.aff")


# Returns the vowel type for a word in the database.
def _get_db_vowel_type(db, wid):
	results = db.query(("SELECT aid FROM flag_attribute_value " +
	                    "WHERE wid = %i AND aid IN (22, 23)") % wid)
	if results.ntuples() == 0: return voikkoutils.VOWEL_DEFAULT
	elif results.ntuples() == 1:
		if results.getresult()[0][0] == 22: return voikkoutils.VOWEL_FRONT
		else: return voikkoutils.VOWEL_BACK
	else: return voikkoutils.VOWEL_BOTH


# Returns the vowel type of inflection suffixes for a word in the database.
def _get_infl_vowel_type(db, wid, word):
	# Check the database
	dbtype = _get_db_vowel_type(db, wid)
	if dbtype != voikkoutils.VOWEL_DEFAULT: return dbtype
	# Check alternative spellings
	altforms_res = db.query('SELECT related_word FROM related_word WHERE wid = %i' % wid)
	for altform_r in altforms_res.getresult():
		altform = unicode(altform_r[0], 'UTF-8')
		if altform.replace(u'|', u'').replace(u'=', u'') == word:
			return voikkoutils.get_wordform_infl_vowel_type(altform)
	# Return the default
	return voikkoutils.get_wordform_infl_vowel_type(word)


WCHARS = u"abcdefghijklmnńoôpqrstuüvwxyzåäöszèéšžáàóABCDEFGHIJKLMNŃOÔPQRSTUÜVWXYZÅÄÖŠŽÈÉŠŽ-'|="
# Checks if string looks like a valid word. This is a mandatory function.
def checkword(string):
	for c in string:
		if not c in WCHARS: return False
	return True


SINGULAR_FORMS = ['nominatiivi', 'genetiivi', 'partitiivi', 'translatiivi', 'essiivi',
                  'inessiivi', 'elatiivi', 'illatiivi', 'adessiivi', 'ablatiivi',
                  'allatiivi', 'abessiivi']
CHARACTERISTIC_NOUN_FORMS = ['nominatiivi', 'genetiivi', 'partitiivi', 'illatiivi',
                             'nominatiivi_mon', 'genetiivi_mon', 'partitiivi_mon', 'illatiivi_mon']
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


# Returns the correct InflectionType for given word.
# classid is the word class identifier in Joukahainen.
# Returns None if no class information could be retrieved
def _get_inflection_type(classid, infclass_main):
	_ensure_infdata_available()
	if classid in [1, 2]: word_types = _NOUN_INFLECTIONS
	elif classid == 3: word_types = _VERB_INFLECTIONS
	else: return None
	
	for word_type in word_types:
		if not infclass_main in word_type.joukahainenClasses: continue
		else: return word_type
	return None

# Returns structure information for the word or the word itself, if
# no structure is available.
def _get_structure_for_word(db, wid, word):
	sql = ("SELECT r.related_word FROM related_word r, word w WHERE " +
	       "w.wid = r.wid AND r.wid = %i AND " +
	       "replace(replace(related_word, '=', ''), '|', '') = w.word") \
	      % wid
	results = db.query(sql)
	if results.ntuples() != 1: return word
	return unicode(results.getresult()[0][0], 'UTF-8')

# Inflection table for a Finnish noun or verb.
def word_inflection(db, wid, word, classid):
	if classid in [1, 2]: characteristic_forms = CHARACTERISTIC_NOUN_FORMS
	elif classid == 3: characteristic_forms = CHARACTERISTIC_VERB_FORMS
	else: return u"(ei taivutuksia tämän sanaluokan sanoille)"
	
	infclass_parts = _get_inflection_gradation(db, wid)
	if infclass_parts == None: return u"(ei taivutusluokkaa)"
	(infclass_main, grad_type) = infclass_parts
	
	word_class = _get_inflection_type(classid, infclass_main)
	if word_class == None: return "(taivutuksia ei ole saatavilla tai virheellinen taivutusluokka)"
	
	wordWithStructure = _get_structure_for_word(db, wid, word)
	tableid = u"inftable%i" % wid
	retdata = u''
	note = u''
	have_only_characteristic = True
	inflected_words = voikkoinfl.inflectWordWithType(wordWithStructure, word_class, infclass_main, grad_type,
	                                                 _get_infl_vowel_type(db, wid, word))
	if inflected_words == []: return "(virhe taivutusten muodostuksessa)"
	
	if classid in [1, 2] and \
	   db.query("SELECT count(*) FROM flag_attribute_value WHERE aid = 37 AND wid = %i" \
	   % wid).getresult()[0][0] == 1: no_singular = True
	else: no_singular = False
	
	previous_inflected = voikkoinfl.InflectedWord()
	inflist = []
	inflected_words.append(voikkoinfl.InflectedWord())
	for inflected_word in inflected_words:
		if no_singular and inflected_word.formName in SINGULAR_FORMS: continue
		if previous_inflected.formName != inflected_word.formName:
			if previous_inflected.formName != u"" and len(inflist) > 0:
				if previous_inflected.isCharacteristic:
					htmlclass = u' class="characteristic"'
				else:
					htmlclass = ''
					have_only_characteristic = False
				infs = reduce(lambda x, y: u"%s, %s" % (x, y), inflist)
				retdata = retdata + (u"<tr%s><td>%s</td><td>%s</td></tr>\n" %
				          (htmlclass, previous_inflected.formName, infs))
			inflist = []
			previous_inflected = inflected_word
		if not inflected_word.inflectedWord in inflist:
			inflist.append(inflected_word.inflectedWord)
	note = word_class.note
	
	table_header = u'<table class="inflection" id="%s">\n<tr><th colspan="2">' % tableid
	if not have_only_characteristic:
		table_header = table_header \
		               + u'<a href="javascript:switchDetailedDisplay(\'%s\');" id="%s"></a>' \
			     % (tableid, tableid + u'a')
	table_header = table_header + u'Taivutus</th></tr>\n'
	if note == u'': notetext = u''
	else: notetext = u'<p>%s</p>\n' % note
	return notetext + table_header + retdata + u'</table>\n'

def _get_xml_flags(flags, flagType, flagMap):
	results = []
	for flagId in flags:
		if flagId in flagMap:
			flag = flagMap[flagId]
			if flag.xmlGroup == flagType:
				results.append(u'<flag>%s</flag>' % flag.xmlFlag)
	return results

def _write_xml_forms(db, req, wid, word):
	altforms_res = db.query('SELECT related_word FROM related_word ' \
	                        + 'WHERE wid = %i ORDER BY related_word' % wid)
	altforms = []
	base_word = None
	for res in altforms_res.getresult():
		altform = unicode(res[0], 'UTF-8')
		if altform.replace(u"=", u"").replace(u"|", u"") == word: base_word = altform
		else: altforms.append(unicode(res[0], 'UTF-8'))
	if base_word == None and len(altforms) > 0: req.write(u'<!-- ERROR: base form missing -->')
	if base_word != None: altforms = [base_word] + altforms
	if len(altforms) == 0: altforms.append(word)
	req.write('\t<forms>\n')
	for form in altforms:
		req.write((u'\t\t<form>%s</form>\n' % form).encode('UTF-8'))
	req.write('\t</forms>\n')

def _write_xml_classes(req, wid, classid, flags):
	req.write('\t<classes>\n')
	if classid == 1:
		if len(set(flags) & set([11, 12, 13, 14])) > 0:
			if 11 in flags: req.write('\t\t<wclass>pnoun_firstname</wclass>\n')
			if 12 in flags: req.write('\t\t<wclass>pnoun_lastname</wclass>\n')
			if 13 in flags: req.write('\t\t<wclass>pnoun_place</wclass>\n')
			if 14 in flags: req.write('\t\t<wclass>pnoun_misc</wclass>\n')
		else: req.write(u'\t\t<wclass>noun</wclass>\n')
	elif classid == 2:
		if 10 in flags: req.write(u'\t\t<wclass>noun</wclass>\n')
		req.write(u'\t\t<wclass>adjective</wclass>\n')
	elif classid == 3:
		req.write(u'\t\t<wclass>verb</wclass>\n')
	elif classid == 4:
		if len(set(flags) & set([45])) > 0:
			if 45 in flags: req.write('\t\t<wclass>interjection</wclass>\n')
	elif classid == 5:
		req.write(u'\t\t<wclass>prefix</wclass>\n')
	req.write('\t</classes>\n')

def _write_xml_inflection(req, flags, strings, flagMap):
	elements = []
	
	for s in strings:
		if s[0] == 1: elements.append(u'<infclass>%s</infclass>' % s[1])
		if s[0] == 16: elements.append(u'<infclass type="historical">%s</infclass>' % s[1])
	
	if 22 in flags:
		if 23 in flags: elements.append(u'<vtype>aä</vtype>')
		else: elements.append(u'<vtype>ä</vtype>')
	elif 23 in flags: elements.append(u'<vtype>a</vtype>')
	
	for f in _get_xml_flags(flags, 'inflection', flagMap): elements.append(f)
	
	if len(elements) > 0:
		req.write('\t<inflection>\n')
		for element in elements:
			req.write('\t\t%s\n' % element.encode('UTF-8'))
		req.write('\t</inflection>\n')

def _write_xml_flagset(req, flags, flagMap, flagname):
	elements = _get_xml_flags(flags, flagname, flagMap)
	if len(elements) > 0:
		req.write('\t<%s>\n' % flagname)
		for element in elements:
			req.write('\t\t%s\n' % element.encode('UTF-8'))
		req.write('\t</%s>\n' % flagname)

def _write_xml_frequency(req, flags, integers, flagMap):
	elements = []
	
	for i in integers:
		if i[0] == 38: elements.append(u'<fclass>%i</fclass>' % i[1])
	
	for f in _get_xml_flags(flags, 'frequency', flagMap): elements.append(f)
	
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

def _write_xml_baseform(req, strings):
	for s in strings:
		if s[0] == 46:
			req.write('\t<baseform>')
			req.write(xml.sax.saxutils.escape(s[1]))
			req.write('</baseform>\n')

def _write_xml_word(db, req, wid, word, wclass, flagMap):
	req.write('<word id="w%i">\n' % wid)
	
	# Read attribute values. We use this strange union query because it is faster
	# than querying different attribute types separately.
	results = db.query("SELECT s.aid, s.value, NULL FROM string_attribute_value s " \
	                 + "WHERE s.wid = %i UNION " % wid \
		       + "SELECT i.aid, NULL, i.value FROM int_attribute_value i " \
		       + "WHERE i.wid = %i UNION " % wid \
		       + "SELECT f.aid, NULL, NULL FROM flag_attribute_value f " \
		       + "WHERE f.wid = %i ORDER BY 1" % wid).getresult()
	strings = []
	integers = []
	flags = []
	for r in results:
		if r[1] != None: strings.append((r[0], unicode(r[1], 'UTF-8')))
		elif r[2] != None: integers.append((r[0], r[2]))
		else: flags.append(r[0])
	
	_write_xml_forms(db, req, wid, word)
	_write_xml_baseform(req, strings)
	_write_xml_classes(req, wid, wclass, flags)
	_write_xml_inflection(req, flags, strings, flagMap)
	_write_xml_flagset(req, flags, flagMap, 'usage')
	_write_xml_flagset(req, flags, flagMap, 'compounding')
	_write_xml_flagset(req, flags, flagMap, 'derivation')
	_write_xml_flagset(req, flags, flagMap, 'style')
	_write_xml_flagset(req, flags, flagMap, 'application')
	_write_xml_frequency(req, flags, integers, flagMap)
	_write_xml_info(req, strings)
	
	req.write('</word>\n')

def _convertFlagMapKeysToJoukahainenId(originalMap):
	"""Converts a map of flags with arbitary keys to map of
	flags with Joukahainen id numbers as keys."""
	mapById = {}
	for (key, flag) in originalMap.iteritems():
		mapById[flag.joukahainen] = flag
	return mapById

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
  package). For more information, see http://joukahainen.puimula.org

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
	
	flagMapByName = voikkoutils.readFlagAttributes(VOIKKO_DATA + "/words/flags.txt")
	flagMap = _convertFlagMapKeysToJoukahainenId(flagMapByName)
	
	results = db.query(("SELECT w.wid, w.word, w.class FROM (%s) w " +
	"WHERE w.wid NOT IN (SELECT f.wid FROM flag_attribute_value f " +
	" WHERE f.aid IN (24, 26)) " +
	"ORDER BY w.wid") % query)
	for result in results.getresult():
		wid = result[0]
		word = unicode(result[1], 'UTF-8')
		wclass = result[2]
		_write_xml_word(db, req, wid, word, wclass, flagMap)
	
	req.write("</wordlist>\n")


# Lists the language specific output types. This is a mandatory function
def jooutput_list_supported_types():
	types = []
	types.append(('xml', u'Tulosta XML-muodossa'))
	return types

# Language specific list output. This is a mandatory function
def jooutput_call(req, outputtype, db, query):
	if outputtype == 'xml':
		_jooutput_xml(req, db, query)
	else:
		joheaders.error_page(req, _(u'Unsupported output type'))

# Returns information about the classification of the word in the format used by
# the Research Institute for the Languages of Finland
def kotus_class(db, wid, word, classid):
	infclass_parts = _get_inflection_gradation(db, wid)
	if infclass_parts == None: return u""
	(infclass_main, grad_type) = infclass_parts
	
	word_class = _get_inflection_type(classid, infclass_main)
	if word_class == None: return ""
	
	return u'<span class="fheader">Kotus-luokka:</span> <span class="fsvalue">%s</span>' \
	       % (reduce(lambda x, y: u"%s, %s" % (x, y), word_class.kotusClasses) + \
	          word_class.kotusGradClass(word, grad_type))

# Returns a link target of the inflection class finder for a word or None,
# if no finder is available
def find_infclass(db, word, classid):
	if classid in [1, 2]: finderclass = 1
	elif classid == 3: finderclass = 3
	else: return None
	return u"'/findclass/classlist?word=%s&class=%i'" % (word, finderclass)
