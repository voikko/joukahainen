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
import voikkoutils
import voikkoinfl
import joheaders
import jotools
import jooutput
import jodb

# Path to Voikko data directory
VOIKKO_DATA = voikkoutils.get_preference('voikko_data_dir')

def _display_form(req, classid, grad_type, word):
	jotools.write(req, u'''
<div class="rightinfo">
<h2>Astevaihteluluokat</h2>
<p>Vastaavat Kotus-astevaihteluluokat suluissa luokan nimen perässä. Joukahaisen
  astevaihteluluokista parittomissa sanan perusmuoto on vahva-asteinen, parillisissa
  heikkoasteinen.</p>
<dl>
<dt>av1 (A, B, C, E, F, G, H, I, J, K, M)</dt><dd>
  tt->t: ma<em>tt</em>o->ma<em>t</em>on<br />

  pp->p: kaa<em>pp</em>i->kaa<em>p</em>in<br />
  kk->k: ruu<em>kk</em>u->ruu<em>k</em>un<br />
  mp->mm: so<em>mp</em>a->so<em>mm</em>an<br />

  p->v: ta<em>p</em>a->ta<em>v</em>an<br />
  nt->nn: ku<em>nt</em>a->ku<em>nn</em>an<br />
  lt->ll: ki<em>lt</em>a->ki<em>ll</em>an<br />

  rt->rr: ke<em>rt</em>a->ke<em>rr</em>an<br />
  t->d: pöy<em>t</em>ä->pöy<em>d</em>än<br />
  nk->ng: ha<em>nk</em>o->ha<em>ng</em>on<br />

  uku->uvu: p<em>uku</em>->p<em>uvu</em>n<br />
  yky->yvy: k<em>yky</em>->k<em>yvy</em>n
</dd>
<dt>av2 (A, B, C, E, F, G, H, I, J, K)</dt><dd>
  t->tt: rii<em>t</em>e->rii<em>tt</em>een<br />

  p->pp: o<em>p</em>as->o<em>pp</em>aan<br />
  k->kk: lii<em>k</em>e->lii<em>kk</em>een<br />
  mm->mp: lu<em>mm</em>e->lu<em>mp</em>een<br />

  v->p: tar<em>v</em>e->tar<em>p</em>een<br />
  nn->nt: ra<em>nn</em>e->ra<em>nt</em>een<br />
  ll->lt: sive<em>ll</em>in->sive<em>lt</em>imen<br />

  rr->rt: va<em>rr</em>as->va<em>rt</em>aan<br />
  d->t: sa<em>d</em>e->sa<em>t</em>een<br />
  ng->nk: ka<em>ng</em>as->ka<em>nk</em>aan<br />

  b->bb: lo<em>b</em>ata->lo<em>bb</em>aan<br />
  g->gg: di<em>g</em>ata->di<em>gg</em>aan
</dd>
<dt>av3 (L)</dt><dd>
  k->j: jär<em>k</em>i->jär<em>j</em>en
</dd>
<dt>av4 (L)</dt><dd>
  j->k: pal<em>j</em>e->pal<em>k</em>een

</dd>
<dt>av5 (D)</dt><dd>
  k->&empty;: vuo<em>k</em>a->vuoan
</dd>
<dt>av6 (D)</dt><dd>
  &empty;->k: säie->säi<em>k</em>een
</dd>
</dl>

</div>
<form method="get" action="classlist"><p>
<label>Sana: <input type="text" name="word" value="%s"/></label><br />
<label>Sanaluokka: <select name="class">''' % word)
	if classid == 3:
		jotools.write(req, u'''
<option value="1">Nomini</option>
<option selected="selected" value="3">Verbi</option>''')
	else:
		jotools.write(req, u'''
<option selected="selected" value="1">Nomini</option>
<option value="3">Verbi</option>''')
	jotools.write(req, u'''
</select></label><br />
<label>Astevaihteluluokka: <select name="gclass">''')
	if grad_type == u'-':
		jotools.write(req, u'<option selected="selected" value="-">ei astevaihtelua</option>')
	else:
		jotools.write(req, u'<option value="-">ei astevaihtelua</option>')
	for i in range(1, 7):
		if grad_type == (u'av%i' % i):
			jotools.write(req, u'<option selected="selected" ' \
			              + (u'value="av%i">av%i</option>' % (i, i)))
		else:
			jotools.write(req, u'<option value="av%i">av%i</option>' % (i, i))
	jotools.write(req, u'''
</select></label><br />
<input type="submit" value="Hae mahdolliset taivutukset" /></p>
</form>''')

def classlist(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	joheaders.page_header_navbar_level1(req, u'Etsi sanalle taivutusluokka', uid, uname)
	
	word = jotools.get_param(req, 'word', u'')
	if not jotools.checkword(word):
		joheaders.error_page(req, u'Sanassa on kiellettyjä merkkejä')
		return '\n'
	
	# Sanaa ei annettu, joten näytetään pelkkä lomake
	if len(word) == 0:
		_display_form(req, 1, u'-', u'')
		joheaders.page_footer_plain(req)
		return '\n'
	
	classid = jotools.toint(jotools.get_param(req, 'class', u'0'))
	if classid == 1:
		classdatafile = VOIKKO_DATA + "/subst.aff"
	elif classid == 3:
		classdatafile = VOIKKO_DATA + "/verb.aff"
	elif classid == 0:
		joheaders.page_footer_plain(req)
		return '\n'
	else:
		joheaders.error_page(req, u'Sanaluokkaa ei ole olemassa')
		return '\n'
	
	grad_type = jotools.get_param(req, 'gclass', u'-')
	if not grad_type in [u'-', u'av1', u'av2', u'av3', u'av4', u'av5', u'av6']:
		joheaders.error_page(req, u'Taivutusluokkaa ei ole olemassa')
		return '\n'
	if grad_type == u'-':
		grad_type_s = u''
	else:
		grad_type_s = u'-' + grad_type
	
	_display_form(req, classid, grad_type, word)
	
	word_classes = voikkoinfl.readInflectionTypes(classdatafile)
	
	for word_class in word_classes:
		if len(word_class.joukahainenClasses) == 0: continue
		infclass_main = word_class.joukahainenClasses[0]
		inflected_words = voikkoinfl.inflectWordWithType(word, word_class, infclass_main, grad_type)
		if inflected_words == []: continue
		
		previous_inflected = voikkoinfl.InflectedWord()
		inflist = []
		inflected_words.append(voikkoinfl.InflectedWord())
		jotools.write(req, '<hr /><h2 class="infclass">' + infclass_main + grad_type_s + '</h2>')
		if word_class.note != u'':
			jotools.write(req, u'<p>%s</p>\n' % word_class.note)
		jotools.write(req, u'<p>Kotus-luokka: %s</p>' % \
		              reduce(lambda x, y: u"%s, %s" % (x, y), word_class.kotusClasses))
		
		jotools.write(req, u'<table class="border">\n')
		for inflected_word in inflected_words:
			if previous_inflected.formName != inflected_word.formName:
				if previous_inflected.formName != u"" and len(inflist) > 0:
					if previous_inflected.isCharacteristic:
						infs = reduce(lambda x, y: u"%s, %s" % (x, y), inflist)
						jotools.write(req, (u"<tr><td>%s</td><td>%s</td></tr>\n" %
						          (previous_inflected.formName, infs)))
				inflist = []
				previous_inflected = inflected_word
			if not inflected_word.inflectedWord in inflist:
				inflist.append(inflected_word.inflectedWord)
		jotools.write(req, u'</table>\n')
	joheaders.page_footer_plain(req)
	return '\n'
