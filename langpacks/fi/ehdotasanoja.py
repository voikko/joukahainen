# -*- coding: utf-8 -*-

# Copyright 2007 Harri Pitkänen (hatapitk@iki.fi)
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

# This file contains tools for the public to suggest missing words

from mod_python import apache

import _apply_config
import _config
import joheaders
import jotools
import jodb
import datetime

def _get_special_vocabularies(db):
	"Returns a list of special vocabularies"
	results = db.query("SELECT descr FROM attribute WHERE type=2 AND " +
	                   "descr like 'ala: %' order by descr")
	svlist = []
	for res in results.getresult():
		svlist.append(unicode(res[0], 'UTF-8'))
	return svlist

def _allow_new_word(req, privdb, substract_from_quota):
	"Checks if a guest user is allowed to add new suggestions"
	current_ip = req.connection.remote_ip
	new_date = datetime.date.today().isoformat()
	if substract_from_quota: privdb.query("BEGIN")
	results = privdb.query("SELECT last_access_date, access_count FROM guestaccess " +
	                       "WHERE ip = '%s'" % current_ip)
	
	if results.ntuples() > 0:
		add_record = False
		last_access_date = results.getresult()[0][0]
		access_count = results.getresult()[0][1]
		if last_access_date == new_date:
			if access_count >= 20:
				if substract_from_quota: privdb.query("COMMIT")
				return False
			else:
				new_access_count = access_count + 1
		else:
			new_access_count = 1
	else:
		add_record = True
	
	if substract_from_quota:
		if results.ntuples() == 0:
			privdb.query("INSERT INTO guestaccess(ip) VALUES('%s')" % current_ip)
		else:
			privdb.query(("UPDATE guestaccess SET last_access_date = '%s', " + \
			              "access_count = %i WHERE ip = '%s'") % \
				   (new_date, new_access_count, current_ip))
		privdb.query("COMMIT")
	return True

def _is_old_word(req, db, word):
	"Checks if given word should be rejected. Returns an error message or None, if word is OK."
	results = db.query("SELECT word FROM raw_word WHERE word = '%s'" \
	                   % jotools.escape_sql_string(word))
	if results.ntuples() > 0: return u"Sanaa on jo ehdotettu lisättäväksi."
	results = db.query("SELECT word FROM word WHERE word = '%s'" \
	                   % jotools.escape_sql_string(word))
	if results.ntuples() > 0: return u'<a href="query/wlist?word=%s">Sana on jo tietokannassa</a>.' \
	                          % jotools.escape_url(word.encode('UTF-8'))
	return None

def _print_entry_form(req, db):
	"Prints an entry form for word suggestions"
	jotools.write(req, u'''<p>Jos Voikko ei tunnista jotain sanaa, voit ehdottaa sen lisäämistä
alla olevan lomakkeen avulla. Sanaa ei lisätä sanastoon automaattisesti, vaan jonkun Joukahaisen
rekisteröityneistä käyttäjistä on ensin käsiteltävä ehdotus.</p>

<p>Sanaston puutteista ja muista ongelmista voi ilmoittaa myös sähköpostitse osoitteeseen hatapitk@iki.fi.</p>

<form method="post" action="ehdotasanoja">

<p><label>Lisättävä sana: <input type="text" name="word" size="30" /></label><br />
<i>Lisättävä sana on parasta kirjoittaa perusmuodossaan. Tämä ei kuitenkaan ole välttämätöntä,
jos olet epävarma sanan oikeasta perusmuodosta.</i></p>

<p><label>Sanan tyyppi: <select name="type">
<option selected="selected" value="yleiskieltä">yleiskielinen sana</option>''')
	for sv in _get_special_vocabularies(db):
		jotools.write(req, u'<option value="%s">%s</option>' % (sv, sv))
	jotools.write(req, u'''
<option value="virheellinen">virheellinen sana (poistettava sanastosta)</option>
</select></label><br />
<i>Valitse lisättävän sanan tyyppi. Vaihtoehtoisesti voit valita kohdan "virheellinen sana",
jos Voikko hyväksyy sanan, jota sen ei mielestäsi pitäisi hyväksyä.</i></p>

<p><label>Lisätietoja: <input type="text" name="comment" size="60" /></label><br />
<i>Tähän voit kirjoittaa sanaan liittyviä lisätietoja. Jos sana on vaikkapa jonkin
erikoisalan termi, kirjoita tähän sille lyhyt selitys.</i></p>

<p><input type="submit" value="Lähetä ehdotus" /></p>
</form>''')

def _print_error_forbidden(req):
	"Print an error, if adding new words is no longer possible"
	jotools.write(req, u'''
<p>Et voi (enää) ehdottaa uusia lisättäviä sanoja. Tarkista seuraavat asiat:</p>
<ul>
<li>Oletko jo ehdottanut 20 sanaa tämän päivän aikana? Väärinkäytösten estämiseksi
rekisteröitymättömät käyttäjät eivät voi tehdä enempää ehdotuksia yhden vuorokauden
aikana. Jos sinulla on enemmän ehdotuksia lisättäviksi tai poistettaviksi sanoiksi,
yritä huomenna uudelleen, tai lähetä ehdotuksesi sähköpostitse yhteystiedoissa mainittuun
osoitteeseen.</li>
<li>Onko joku muu käyttänyt tänään tätä palvelua samalta koneelta kuin sinä, tai onko
Internet-selaimesi asetettu käyttämään välityspalvelinta? Rekisteröitymättömien käyttäjien
rajoitukset tehdään koneen ip-osoitteen perusteella, joten joku muu on
ehkä jo käyttänyt päivittäisen lisäyskiintiösi. Pahoittelemme ongelmaa, mutta meillä ei
ole mahdollisuutta käyttää älykkäämpien rajoitusmenetelmiä. Voit lähettää lisäysehdotuksesi
sähköpostitse.</li>
</ul>
<p>Jos sinulla on käyttäjätunnus Joukahaiseen, kirjautumalla sisään pääset käyttämään
tätä palvelua rajoituksetta. Rekisteröityneiden käyttäjien tulisi kuitenkin mieluummin
lisätä sanat suoraan sanastotietokantaan.</p>''')

def index(req):
	db = jodb.connect()
	privdb = jodb.connect_private()
	(uid, uname, editable) = jotools.get_login_user(req)
	joheaders.page_header_navbar_level1(req, u"Ehdota uusia sanoja", uid, uname)
	
	word = jotools.get_param(req, "word", u"").strip()
	wtype = jotools.get_param(req, "type", u"").strip()
	comment = jotools.get_param(req, "comment", u"").strip()
	
	if word != u"":
		if not jotools.checkword(word):
			jotools.write(req, u'<p class="error">Sanassa on kiellettyjä merkkejä.</p>')
			_print_entry_form(req, db)
		else:
			db.query("BEGIN")
			error = _is_old_word(req, db, word)
			if error != None:
				jotools.write(req, u'<p class="error">%s</p>' % error)
				_print_entry_form(req, db)
			elif not (editable or _allow_new_word(req, privdb, True)):
				_print_error_forbidden(req)
			else:
				db.query("INSERT INTO raw_word(word, info, notes) " +
				         "VALUES('%s', '%s', '%s')" % \
				         (jotools.escape_sql_string(word),
				          jotools.escape_sql_string(wtype),
				          jotools.escape_sql_string(comment)))
				jotools.write(req, u'<p class="ok">Ehdotuksesi on tallennettu. ' +
				                   u'Kiitos avusta!</p>')
				_print_entry_form(req, db)
			db.query("COMMIT")
	
	elif editable or _allow_new_word(req, privdb, False):
		_print_entry_form(req, db)
	else:
		_print_error_forbidden(req)
	joheaders.page_footer_plain(req)
	return '\n'
