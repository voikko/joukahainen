# -*- coding: utf-8 -*-

# Copyright 2007 - 2023 Harri Pitkänen (hatapitk@iki.fi)
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

# This file contains tools for the public to suggest missing words

import joheaders
import jotools
import jodb
import datetime
from flask import request

def _get_special_vocabularies(db):
	"Returns a list of special vocabularies"
	results = db.query("SELECT descr FROM attribute WHERE type=2 AND " +
	                   "descr like 'ala: %' order by descr")
	svlist = []
	for res in results.getresult():
		svlist.append(res[0])
	return svlist

def _get_remote_address():
	if 'X-Forwarded-For' in request.headers:
		return request.headers.getlist("X-Forwarded-For")[0].rpartition(' ')[-1]
	return request.remote_addr or 'untrackable'

def _allow_new_word(req, privdb, substract_from_quota):
	"Checks if a guest user is allowed to add new suggestions"
	current_ip = _get_remote_address()
	new_date = datetime.date.today().isoformat()
	if substract_from_quota: privdb.query("BEGIN")
	results = privdb.query("SELECT last_access_date, access_count FROM guestaccess " +
	                       "WHERE ip = $1", (current_ip,))
	
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
			privdb.query("INSERT INTO guestaccess(ip) VALUES($1)", (current_ip,))
		else:
			privdb.query(("UPDATE guestaccess SET last_access_date = $1, " + \
			              "access_count = $2 WHERE ip = $3"), \
				   (new_date, new_access_count, current_ip))
		privdb.query("COMMIT")
	return True

def _is_old_word(req, db, word):
	"Checks if given word should be rejected. Returns an error message or None, if word is OK."
	
	# Previously suggested words
	results = db.query("SELECT word FROM raw_word WHERE word = $1", (word,))
	if results.ntuples() > 0: return "Sanaa on jo ehdotettu lisättäväksi."
	
	# Words in database
	results = db.query("SELECT word FROM word WHERE word = $1", (word,))
	if results.ntuples() > 0: return '<a href="query/wlist?word=%s">Sana on jo tietokannassa</a>.' \
	                          % jotools.escape_url(word.encode('UTF-8'))
	
	# Alternative spellings
	results = db.query("SELECT wid FROM related_word WHERE replace(replace(related_word, " +
	                   "'=', ''), '|', '') LIKE $1", (word,))
	if results.ntuples() > 0: return '<a href="word/edit?wid=%i">Sana on jo tietokannassa</a>.' \
	                          % results.getresult()[0][0]
	
	return None

def _print_entry_form(req, db):
	"Prints an entry form for word suggestions"
	jotools.write(req, '''<p>Joukahainen on Voikko-oikolukuohjelmiston kehittäjien
yhteinen sanastotietokanta. Sen avulla myös Voikon käyttäjät voivat auttaa kehittäjiä tekemään ohjelmasta
entistäkin paremman. Esimerkiksi LibreOfficea käyttäessäsi saatat joskus huomata, että
oikolukutoiminto ei hyväksy jotain kirjoittamaasi sanaa, vaikka se on oikein. Voit ilmoittaa meille
näistä sanoista tämän lomakkeen kautta.</p>

<form method="post" action="ehdotasanoja">

<p><label>Lisättävä sana: <input type="text" name="word" size="30" /></label><br />
<i>Lisättävä sana on parasta kirjoittaa perusmuodossaan. Tämä ei kuitenkaan ole välttämätöntä,
jos olet epävarma sanan oikeasta perusmuodosta.</i></p>

<p><label>Sanan tyyppi: <select name="type">
<option selected="selected" value="yleiskieltä">yleiskielinen sana</option>''')
	for sv in _get_special_vocabularies(db):
		jotools.write(req, '<option value="%s">%s</option>' % (sv, sv))
	jotools.write(req, '''
<option value="virheellinen">virheellinen sana (poistettava sanastosta)</option>
</select></label><br />
<i>Valitse lisättävän sanan tyyppi. Vaihtoehtoisesti voit valita kohdan "virheellinen sana",
jos Voikko hyväksyy virheellisen sanan.</i></p>

<p><label>Lisätietoja: <input type="text" name="comment" size="60" /></label><br />
<i>Tähän voit kirjoittaa sanaan liittyviä lisätietoja. Jos sana on jonkin
erikoisalan termi tai muuten harvinainen, kirjoita tähän sille lyhyt selitys.</i></p>

<p><input type="submit" value="Lähetä ehdotus" /></p>
</form>
<hr />
<p>Ehdotukset käsitellään yleensä parin päivän kuluessa niiden lähettämisestä. Päivitettyjä
versioita Voikon sanastosta julkaistaan puolestaan noin puolen vuoden välein.
Jos sinulla on paljon ehdotuksia sanastoon lisättäviksi sanoiksi tai haluat auttaa
jonkin erikoisalan sanaston kehityksessä, voit myös lähettää ehdotuksesi sähköpostitse Harri Pitkäselle
(<a href="mailto:hatapitk@iki.fi">hatapitk@iki.fi</a>).</p>

<p>Voikkoa kehitetään pääasiassa vapaaehtoisvoimin. Lisää tietoa Voikosta löytyy
osoitteesta <a href="https://voikko.puimula.org">voikko.puimula.org</a>.</p>''')

def _print_error_forbidden(req):
	"Print an error, if adding new words is no longer possible"
	jotools.write(req, '''
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
ole mahdollisuutta käyttää älykkäämpiä rajoitusmenetelmiä. Voit lähettää lisäysehdotuksesi
sähköpostitse.</li>
</ul>
<p>Jos sinulla on käyttäjätunnus Joukahaiseen, kirjautumalla sisään pääset käyttämään
tätä palvelua rajoituksetta. Rekisteröityneiden käyttäjien tulisi kuitenkin mieluummin
lisätä sanat suoraan sanastotietokantaan.</p>''')

def ehdotasanoja_index(req):
	db = jodb.connect()
	privdb = jodb.connect_private()
	(uid, uname, editable) = jotools.get_login_user(req)
	joheaders.page_header_navbar_level1(req, "Ehdota uusia sanoja", uid, uname)
	
	if request.method == 'GET':
		if editable or _allow_new_word(req, privdb, False):
			_print_entry_form(req, db)
		else:
			_print_error_forbidden(req)
	elif request.method == 'POST':
		word = jotools.get_param(req, "word", "").strip()
		wtype = jotools.get_param(req, "type", "").strip()
		comment = jotools.get_param(req, "comment", "").strip()

		if word == "":
			jotools.write(req, '<p class="error">Sana ei saa olla tyhjä.</p>')
			_print_entry_form(req, db)
		elif not jotools.checkword(word):
			jotools.write(req, '<p class="error">Sanassa on kiellettyjä merkkejä.</p>')
			_print_entry_form(req, db)
		else:
			db.query("BEGIN")
			error = _is_old_word(req, db, word)
			if error != None:
				jotools.write(req, '<p class="error">%s</p>' % error)
				_print_entry_form(req, db)
			elif not (editable or _allow_new_word(req, privdb, True)):
				_print_error_forbidden(req)
			else:
				db.query("INSERT INTO raw_word(word, info, notes) " +
				         "VALUES($1, $2, $3)", \
				         (word, wtype, comment))
				jotools.write(req, '<p class="ok">Ehdotuksesi on tallennettu. ' +
				                   'Kiitos avusta!</p>')
				_print_entry_form(req, db)
			db.query("COMMIT")
	
	elif editable or _allow_new_word(req, privdb, False):
		_print_entry_form(req, db)
	else:
		_print_error_forbidden(req)
	joheaders.page_footer_plain(req)
	return '\n'
