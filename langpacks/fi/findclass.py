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

# Path to Hunspell-fi data directory
HF_DATA = '/home/harri/hunspell-fi/svn/trunk/data'

CHARACTERISTIC_NOUN_FORMS = ['nominatiivi', 'genetiivi', 'partitiivi', 'illatiivi',
                             'genetiivi_mon', 'partitiivi_mon', 'illatiivi_mon']
CHARACTERISTIC_VERB_FORMS = ['infinitiivi_1', 'preesens_yks_1', 'imperfekti_yks_3',
                             'kondit_yks_3', 'imperatiivi_yks_3', 'partisiippi_2',
                             'imperfekti_pass']
def classlist(req):
	joheaders.page_header(req, u'Etsi sanalle taivutusluokka')
	jotools.write(req, u'''
<div class="main">
<div class="rightinfo">
<h2>Astevaihteluluokat</h2>
<dl>
<dt>av1</dt><dd>
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
<dt>av2</dt><dd>
  t->tt: rii<em>t</em>e->rii<em>tt</em>een<br />

  p->pp: o<em>p</em>as->o<em>pp</em>aan<br />
  k->kk: lii<em>k</em>e->lii<em>kk</em>een<br />
  mm->mp: lu<em>mm</em>e->lu<em>mp</em>een<br />

  v->p: tar<em>v</em>e->tar<em>p</em>een<br />
  nn->nt: ra<em>nn</em>e->ra<em>nt</em>een<br />
  ll->lt: sive<em>ll</em>in->sive<em>lt</em>imen<br />

  rr->rt: va<em>rr</em>as->va<em>rt</em>aan<br />
  d->t: sa<em>d</em>e->sa<em>t</em>een<br />
  ng->nk: ka<em>ng</em>as->ka<em>nk</em>aan

</dd>
<dt>av3</dt><dd>
  k->j: jär<em>k</em>i->jär<em>j</em>en
</dd>
<dt>av4</dt><dd>
  j->k: pal<em>j</em>e->pal<em>k</em>een

</dd>
<dt>av5</dt><dd>
  k->&empty;: vuo<em>k</em>a->vuoan
</dd>
<dt>av6</dt><dd>
  &empty;->k: säie->säi<em>k</em>een
</dd>
</dl>

</div>
<form method="get" action="classlist"><p>
<label>Sana: <input type="text" name="word" /></label><br />
<label>Sanaluokka: <select name="class">
<option selected="selected" value="1">Nomini</option>
<option value="3">Verbi</option>
</select></label><br />
<label>Astevaihteluluokka: <select name="gclass">
<option selected="selected" value="">ei astevaihtelua</option>
<option value="av1">av1</option>
<option value="av2">av2</option>
<option value="av3">av3</option>
<option value="av4">av4</option>
<option value="av5">av5</option>
<option value="av6">av6</option>
</select></label><br />
<input type="submit" value="Hae mahdolliset taivutukset" /></p>
</form>''')
	classid = jotools.toint(jotools.get_param(req, 'class', u'0'))
	if classid == 1:
		classdatafile = HF_DATA + "/subst.aff"
		characteristic_forms = CHARACTERISTIC_NOUN_FORMS
	elif classid == 3:
		classdatafile = HF_DATA + "/verb.aff"
		characteristic_forms = CHARACTERISTIC_VERB_FORMS
	elif classid == 0:
		jotools.write(req, "</div>\n")
		joheaders.page_footer(req)
		return "</html>"
	else:
		joheaders.error_page(req, u'Sanaluokkaa ei ole olemassa')
		return '\n'
	
	word = jotools.get_param(req, 'word', u'')
	if len(word) == 0:
		jotools.write(req, "</div>\n")
		joheaders.page_footer(req)
		return "</html>"
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
	jotools.write(req, "</div>\n")
	joheaders.page_footer(req)
	return "</html>"
