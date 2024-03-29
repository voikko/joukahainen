from flask import Flask, request, Response, send_file
from _pg import ProgrammingError
import jodb
import jotools
import joheaders
import joeditors
import jooutput
import word as joword
import re
import random
import hashlib
import time
import datetime
import _config
import os
from functools import reduce
from ehdotasanoja import ehdotasanoja_index
from findclass import classlist

_ = _config.transl

app = Flask(__name__)

@app.route('/')
def index():
    db = jodb.connect()
    req = jotools.Request_wrapper()
    (uid, uname, editable) = jotools.get_login_user(req)
    static_vars = {'UID': uid, 'UNAME': uname, 'EDITABLE': editable}
    jotools.process_template(req, db, static_vars, 'index_index', _config.LANG, 'joindex', 0)
    joheaders.page_footer_plain(req)
    return req.response()

@app.route('/word/edit')
def word_edit():
    req = jotools.Request_wrapper()
    wid = jotools.get_param(req, 'wid', None)
    if (wid == None):
        joheaders.error_page(req, _('Parameter %s is required') % 'wid')
        return req.response()
    wid_n = jotools.toint(wid)
    db = jodb.connect()
    results = db.query("select word, class from word where wid = $1", (wid_n,))
    if results.ntuples() == 0:
        joheaders.error_page(req, _('Word %i does not exist') % wid_n)
        return req.response()
    wordinfo = results.getresult()[0]
    (uid, uname, editable) = jotools.get_login_user(req)
    static_vars = {'WID': wid_n, 'WORD': wordinfo[0], 'CLASSID': wordinfo[1],
                   'UID': uid, 'UNAME': uname, 'EDITABLE': editable}
    jotools.process_template(req, db, static_vars, 'word_edit', _config.LANG, 'joeditors', 1)
    joheaders.page_footer_plain(req)
    return req.response()

@app.route('/word/change', methods = ['POST'])
def change():
    req = jotools.Request_wrapper()
    wid = jotools.get_param(req, 'wid', None)
    (uid, uname, editable) = jotools.get_login_user(req)
    if not editable:
        joheaders.error_page(req, _('You are not allowed to edit data'))
        return req.response()
    if (wid == None):
        joheaders.error_page(req, _('Parameter %s is required') % 'wid')
        return req.response()
    
    wid_n = jotools.toint(wid)
    db = jodb.connect()
    db.query("begin")
    wclass_results = db.query("select class from word where wid = $1", (wid_n,))
    if wclass_results.ntuples() == 0:
        joheaders.error_page(req, _('Word %i does not exist') % wid_n)
        db.query("rollback")
        return req.response()
    wclass = wclass_results.getresult()[0][0]
    edfield_results = db.query("select a.type, a.aid, a.descr from attribute a, attribute_class ac " +
                               "where a.aid = ac.aid and ac.classid = $1 and a.editable = TRUE", (wclass,))
    eid = db.query("select nextval('event_eid_seq')").getresult()[0][0]
    event_inserted = False
    messages = []
    
    for attribute in edfield_results.getresult():
        if attribute[0] == 1: # string attribute
            html_att = 'string%i' % attribute[1]
            newval = jotools.get_param(req, html_att, None)
            if newval == None: continue
            
            vresults = db.query("select s.value from string_attribute_value s where " +
                                "s.wid = $1 and s.aid = $2", (wid_n, attribute[1]))
            if vresults.ntuples() == 0: oldval = ""
            else: oldval = vresults.getresult()[0][0]
            if oldval == newval: continue
            if not event_inserted:
                db.query("insert into event(eid, eword, euser) values($1, $2, $3)", (eid, wid_n, uid))
                event_inserted = True
            if newval == '':
                db.query("delete from string_attribute_value where wid = $1 and aid = $2", (wid_n, attribute[1]))
            elif oldval == '':
                db.query("insert into string_attribute_value(wid, aid, value, eevent) " +
                         "values($1, $2, $3, $4)", (wid_n, attribute[1], newval, eid))
            else:
                db.query("update string_attribute_value set value=$1, eevent=$2 where wid=$3 and aid=$4",
                    (newval, eid, wid_n, attribute[1]))
            messages.append("%s: '%s' -> '%s'" % (attribute[2],
                            oldval, newval))
        if attribute[0] == 3: # integer attribute
            html_att = 'int%i' % attribute[1]
            newval_s = jotools.get_param(req, html_att, None)
            if newval_s == None: continue
            newval_s = newval_s.strip()
            if newval_s == '':
                newval = None
            else:
                try: newval = int(newval_s)
                except ValueError: continue
                # Limit value range to prevent troubles with storing the
                # value into the database
                if newval < -1000000 or newval > 1000000: continue
            
            vresults = db.query("select i.value from int_attribute_value i where " +
                                "i.wid = $1 and i.aid = $2", (wid_n, attribute[1]))
            if vresults.ntuples() == 0: oldval = None
            else: oldval = vresults.getresult()[0][0]
            if oldval == newval: continue
            if not event_inserted:
                db.query("insert into event(eid, eword, euser) values($1, $2, $3)", (eid, wid_n, uid))
                event_inserted = True
            if newval == None:
                db.query("delete from int_attribute_value where wid = $1 and aid = $2", (wid_n, attribute[1]))
            elif oldval == None:
                db.query("insert into int_attribute_value(wid, aid, value, eevent) " +
                         "values($1, $2, $3, $4)", (wid_n, attribute[1], newval, eid))
            else:
                db.query("update int_attribute_value set value=$1, eevent=$2 where wid=$3 and aid=$4",
                    (newval, eid, wid_n, attribute[1]))
            if oldval == None: oldval_s = _('(None)')
            else: oldval_s = repr(oldval)
            if newval == None: newval_s = _('(None)')
            else: newval_s = repr(newval)
            messages.append("%s: %s -> %s" % (attribute[2],
                            oldval_s, newval_s))
    
    comment = jotools.get_param(req, 'comment', '')
    
    if comment != '':
        if not event_inserted:
            db.query("insert into event(eid, eword, euser) values($1, $2, $3)", (eid, wid_n, uid))
            event_inserted = True
        db.query("update event set comment = $1 where eid = $2", (comment, eid))
    if event_inserted and len(messages) > 0:
        mess_str = reduce(lambda x, y: x + "\n" + y, messages, "")
        db.query("update event set message = $1 where eid = $2", (mess_str, eid))
    db.query("commit")
    joheaders.redirect_header(req, 'edit?wid=%i' % wid_n)
    return req.response()

@app.route('/word/flags', methods = ['POST', 'GET'])
def word_flags():
    req = jotools.Request_wrapper()
    wid = jotools.get_param(req, 'wid', None)
    (uid, uname, editable) = jotools.get_login_user(req)
    if not editable:
        joheaders.error_page(req, _('You are not allowed to edit data'))
        return req.response()
    if wid == None:
        joheaders.error_page(req, _('Parameter %s is required') % 'wid')
        return req.response()
    wid_n = jotools.toint(wid)
    db = jodb.connect()
    results = db.query("select word, class from word where wid = $1", (wid_n,))
    if results.ntuples() == 0:
        joheaders.error_page(req, _('Word %i does not exist') % wid_n)
        return req.response()
    wordinfo = results.getresult()[0]
    if request.method == 'GET': # show editor
        word = wordinfo[0]
        classid = wordinfo[1]
        title1 = _('Word') + ': ' + word
        link1 = 'edit?wid=%i' % wid_n
        title2 = _('flags')
        joheaders.page_header_navbar_level2(req, title1, link1, title2, uid, uname, wid_n)
        jotools.write(req, '<p>%s</p>\n' % joeditors.call(db, 'word_class', [classid]))
        jotools.write(req, joeditors.call(db, 'flag_edit_form', [wid_n, classid]))
        joheaders.page_footer_plain(req)
        return req.response()
    db.query("begin")
    edfield_results = db.query("SELECT a.aid, a.descr, CASE WHEN fav.wid IS NULL THEN 'f' ELSE 't' END " +
                        "FROM attribute_class ac, attribute a " +
                        "LEFT OUTER JOIN flag_attribute_value fav ON (a.aid = fav.aid and fav.wid = $1) " +
                        "WHERE a.aid = ac.aid AND ac.classid = $2 AND a.type = 2 " +
                        "ORDER BY a.descr", (wid_n, wordinfo[1]))
    eid = db.query("select nextval('event_eid_seq')").getresult()[0][0]
    event_inserted = False
    messages = []
    
    for attribute in edfield_results.getresult():
        html_att = 'attr%i' % attribute[0]
        if jotools.get_param(req, html_att, '') == 'on': newval = True
        else: newval = False
        
        if attribute[2] == 't': oldval = True
        else: oldval = False
        
        if oldval == newval: continue
        if not event_inserted:
            db.query("insert into event(eid, eword, euser) values($1, $2, $3)", \
                     (eid, wid_n, uid))
            event_inserted = True
        if newval == False:
            db.query("delete from flag_attribute_value where wid = $1 " +
                      "and aid = $2", (wid_n, attribute[0]))
            messages.append(_("Flag removed: '%s'") % attribute[1])
        if newval == True:
            db.query("insert into flag_attribute_value(wid, aid, eevent) " +
                     "values($1, $2, $3)", (wid_n, attribute[0], eid))
            messages.append(_("Flag added: '%s'") % attribute[1])
    
    comment = jotools.get_param(req, 'comment', '')
    
    if comment != '':
        if not event_inserted:
            db.query("insert into event(eid, eword, euser) values($1, $2, $3)", \
                     (eid, wid_n, uid))
            event_inserted = True
        db.query("update event set comment = $1 where eid = $2", (comment, eid))
    if event_inserted and len(messages) > 0:
        mess_str = reduce(lambda x, y: x + "\n" + y, messages, "")
        db.query("update event set message = $1 where eid = $2", (mess_str, eid))
    db.query("commit")
    joheaders.redirect_header(req, 'edit?wid=%i' % wid_n)
    return req.response()

@app.route('/word/rwords', methods = ['POST', 'GET'])
def rwords():
    req = jotools.Request_wrapper()
    wid = jotools.get_param(req, 'wid', None)
    (uid, uname, editable) = jotools.get_login_user(req)
    if not editable:
        joheaders.error_page(req, _('You are not allowed to edit data'))
        return req.response()
    if wid == None:
        joheaders.error_page(req, _('Parameter %s is required') % 'wid')
        return req.response()
    wid_n = jotools.toint(wid)
    db = jodb.connect()
    results = db.query("select word, class from word where wid = $1", (wid_n,))
    if results.ntuples() == 0:
        joheaders.error_page(req, _('Word %i does not exist') % wid_n)
        return req.response()
    wordinfo = results.getresult()[0]
    if request.method == 'GET': # show editor
        word = wordinfo[0]
        classid = wordinfo[1]
        title1 = _('Word') + ': ' + word
        link1 = 'edit?wid=%i' % wid_n
        title2 = _('related words')
        joheaders.page_header_navbar_level2(req, title1, link1, title2, uid, uname, wid_n)
        jotools.write(req, '<p>%s</p>\n' % joeditors.call(db, 'word_class', [classid]))
        jotools.write(req, joeditors.call(db, 'rwords_edit_form', [wid_n]))
        joheaders.page_footer_plain(req)
        return req.response()
    db.query("begin")
    rword_results = db.query("SELECT rwid, related_word FROM related_word WHERE wid = $1", (wid_n,))
    rword_res = rword_results.getresult()
    eid = db.query("select nextval('event_eid_seq')").getresult()[0][0]
    event_inserted = False
    messages = []
    
    for attribute in rword_res:
        html_att = 'rword%i' % attribute[0]
        if jotools.get_param(req, html_att, '') == 'on': remove = True
        else: remove = False
        
        if not remove: continue
        if not event_inserted:
            db.query("insert into event(eid, eword, euser) values($1, $2, $3)", \
                     (eid, wid_n, uid))
            event_inserted = True
        db.query("delete from related_word where wid = $1 and rwid = $2", (wid_n, attribute[0]))
        messages.append(_("Alternative spelling removed: '%s'") % jotools.escape_html(attribute[1]))
    
    newwords = jotools.get_param(req, 'add', '')
    for word in jotools.unique(newwords.split()):
        if not jotools.checkword(word): continue
        already_listed = False
        for attribute in rword_res:
            if word == attribute[1]:
                already_listed = True
                break
        if already_listed: continue
        if not event_inserted:
            db.query("insert into event(eid, eword, euser) values($1, $2, $3)", (eid, wid_n, uid))
            event_inserted = True
        db.query("insert into related_word(wid, eevent, related_word) values($1, $2, $3)", \
                 (wid_n, eid, word))
        messages.append(_("Alternative spelling added: '%s'") % jotools.escape_html(word))
    
    comment = jotools.get_param(req, 'comment', '')
    
    if comment != '':
        if not event_inserted:
            db.query("insert into event(eid, eword, euser) values($1, $2, $3)", (eid, wid_n, uid))
            event_inserted = True
        db.query("update event set comment = $1 where eid = $2", (comment, eid))
    if event_inserted and len(messages) > 0:
        mess_str = reduce(lambda x, y: x + "\n" + y, messages, "")
        db.query("update event set message = $1 where eid = $2", (mess_str, eid))
    db.query("commit")
    joheaders.redirect_header(req, 'edit?wid=%i' % wid_n)
    return req.response()

@app.route('/word/add_manual', methods = ['GET'])
def word_add_manual():
    req = jotools.Request_wrapper()
    (uid, uname, editable) = jotools.get_login_user(req)
    if not editable:
        joheaders.error_page(req, _('You are not allowed to edit data'))
        return req.response()
    db = jodb.connect()
    words_per_page = 15
    joheaders.page_header_navbar_level1(req, _("Add words"), uid, uname)
    jotools.write(req, '<form method="post" action="add">\n' +
                       '<table class="border">\n<tr><th>%s</th><th>%s</th></tr>\n' \
                       % (_('Word'), _('Word class')))
    joword.add_entry_fields(req, db, None, words_per_page)
    jotools.write(req, '</table>\n' +
                       '<p><input type="submit" value="%s"></p></form>\n' % _("Add words"))
    joheaders.page_footer_plain(req)
    return req.response()

@app.route('/word/add', methods = ['POST'])
def word_add():
    req = jotools.Request_wrapper()
    (uid, uname, editable) = jotools.get_login_user(req)
    if not editable:
        joheaders.error_page(req, _('You are not allowed to edit data'))
        return req.response()
    db = jodb.connect()
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
        stored_word = joword.store_word(db, word, uid)
        if stored_word['wid'] != None: added_count = added_count + 1
        if stored_word['try_again']: need_confirm_count = need_confirm_count + 1
        nwordlist.append(stored_word)
    db.query("COMMIT")
    if added_count == 1 and len(nwordlist) == 1:
        # No confirmation screen if exactly 1 word was successfully added
        joheaders.redirect_header(req, "edit?wid=%i" % nwordlist[0]['wid'])
        return req.response()
    joheaders.page_header_navbar_level1(req, _("Add words"), uid, uname)
    if need_confirm_count > 0:
        jotools.write(req, '<p>' + _('''Adding some words failed or requires confirmation.
Make the required changes and mark the words that you still want to add.''') + '</p>')
        jotools.write(req, '<form method="post" action="add">\n')
        jotools.write(req,
          '<table class="border"><tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>\n' \
          % (_('Word'), _('Word class'), _('Confirm addition'), _('Notes')))
        joword.add_entry_fields(req, db, nwordlist, None)
        jotools.write(req, '</table>\n<p>' +
                           '<input type="hidden" name="confirm" value="on">' +
                           '<input type="submit" value="%s"></p></form>\n' % _('Continue'))
        joheaders.page_footer_plain(req)
        return req.response()
    else:
        jotools.write(req, '<p>%s:</p>' % _('The following changes were made'))
        jotools.write(req,
          '<table class="border"><tr><th>%s</th><th>%s</th><th>%s</th></tr>\n' \
          % (_('Word'), _('Word class'), _('Notes')))
        joword.add_entry_fields(req, db, nwordlist, None)
        jotools.write(req, '</table>\n')
        jotools.write(req, '<p><a href="../">%s ...</a></p>\n' \
                           % _('Back to main page'))
        joheaders.page_footer_plain(req)
        return req.response()

@app.route('/word/categories', methods = ['GET'])
def word_categories():
    req = jotools.Request_wrapper()
    (uid, uname, editable) = jotools.get_login_user(req)
    if not editable:
        joheaders.error_page(req, _('You are not allowed to edit data'))
        return req.response()
    db = jodb.connect()
    results = db.query("SELECT coalesce(info, ''), count(*) FROM raw_word " +
                       "WHERE processed = FALSE " +
                       "GROUP BY coalesce(info, '') " +
                       "ORDER BY coalesce(info, '') ")
    if results.ntuples() == 0:
        joheaders.error_page(req, _('There are no words to be added'))
        return req.response()
    joheaders.page_header_navbar_level1(req, _("Add words"), uid, uname)
    jotools.write(req, "<p>%s:</p>\n" \
                       % _('Choose a category from which you want to add words'))
    jotools.write(req, "<table><tr><th>%s</th><th>%s</th></tr>\n" \
                       % (_('Category'), _('Words left')))
    for result in results.getresult():
        cat = result[0]
        if cat == '': cats = '(' + _('no category') + ')'
        else: cats = cat
        jotools.write(req, ('<tr><td><a href="add_from_db?category=%s">%s</a></td>' +
                            '<td>%i</td></tr>\n') \
          % (jotools.escape_url(result[0]), jotools.escape_html(cats), result[1]))
    jotools.write(req, "</table>\n")
    jotools.write(req, '<p><a href="add_from_db">%s ...</a></p>\n' % _('All words'))
    joheaders.page_footer_plain(req)
    return req.response()

@app.route('/word/add_from_db', methods = ['GET'])
def word_add_from_db():
    req = jotools.Request_wrapper()
    (uid, uname, editable) = jotools.get_login_user(req)
    if not editable:
        joheaders.error_page(req, _('You are not allowed to edit data'))
        return req.response()
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
        return req.response()
    if results.ntuples() == 0 and category != None:
        joheaders.error_page(req, _('There are no words to be added') + ' ' +
                  _('in category %s') % jotools.escape_html(category))
        return req.response()
    class_res = db.query("select classid, name from wordclass").getresult()
    joheaders.page_header_navbar_level1(req, _("Add words"), uid, uname)
    jotools.write(req, '<form method="post" action="add">\n')
    jotools.write(req, '<table class="border">\n')
    jotools.write(req, '<tr><th>%s</th><th>%s</th><th>%s</th></tr>\n' \
                       % (_('Word'), _('Word class'), _('Notes')))
    i = 0
    for result in results.getresult():
        word = result[0]
        notes = result[1]
        jotools.write(req, '<tr><td><input type="hidden" name="origword%i" value=%s />' \
                               % (i, jotools.escape_form_value(word)))
        jotools.write(req, '<input type="text" name="word%i" value=%s /></td><td>' \
                           % (i, jotools.escape_form_value(word)))
        jotools.write(req, joword.get_class_selector(class_res, None, i, True))
        jotools.write(req, '</td><td>')
        jotools.write(req, jotools.escape_html(notes))
        jotools.write(req, '</td></tr>\n')
        i = i + 1
    jotools.write(req, '</table>\n' +
                       '<p><input type="submit" value="%s"></p></form>\n' % _("Add words"))
    joheaders.page_footer_plain(req)
    return req.response()

@app.route('/query/form')
def query_form():
    req = jotools.Request_wrapper()
    db = jodb.connect()
    (uid, uname, editable) = jotools.get_login_user(req)
    joheaders.page_header_navbar_level1(req, _('Search database'), uid, uname)
    jotools.write(req, '<form method="get" action="wlist">\n<p>')
    jotools.write(req, '<label>%s: <input type="text" name="word" /></label></p>\n' % _('Word'))
    jotools.write(req, '<p><label><input type="checkbox" name="wordre" /> %s</label>\n' \
                  % _('Use regular expression'))
    jotools.write(req, ' <b>%s</b> <label><input type="checkbox" name="wordsimplere" /> %s</label><br />\n' \
                  % (_('or'), _('Case insensitive search')))
    jotools.write(req, '<label><input type="checkbox" name="altforms" /> %s</label></p>\n' \
                  % _('Search from alternative spellings'))
    
    wclasses = db.query("SELECT classid, name FROM wordclass ORDER BY classid").getresult()
    jotools.write(req, '<h2>%s</h2>\n' % _('Word class'))
    jotools.write(req, '<p>%s ' % _('Word class is'))
    jotools.write(req, '<select name="wordclass">\n')
    jotools.write(req, '<option selected="selected" value="">(%s)</option>\n' % _('any'))
    for (classid, name) in wclasses:
        jotools.write(req, '<option value="%i">%s</option>\n' % (classid, name))
    jotools.write(req, '</select></p>\n')
    
    textattrs = db.query("SELECT aid, descr FROM attribute WHERE type = 1 ORDER BY descr, aid").getresult()
    jotools.write(req, '<h2>%s</h2>\n' % _('Text attributes'))
    jotools.write(req, '<p><select name="textaid">\n')
    jotools.write(req, '<option selected="selected" value="">(%s)</option>\n' % _('select attribute'))
    for (aid, dsc) in textattrs:
        jotools.write(req, '<option value="%i">%s</option>\n' % (aid, dsc))
    jotools.write(req, '</select> %s <input type="text" name="textvalue" /><br />\n' % _('is'))
    
    flagattrs = db.query("SELECT aid, descr FROM attribute WHERE type = 2 ORDER BY descr, aid").getresult()
    jotools.write(req, '</p><h2>%s</h2>' % _('Flags set'))
    jotools.write(req, '<ul class="cblist">')
    for (aid, dsc) in flagattrs:
        jotools.write(req, '<li><label><input type="checkbox" name="flagon%i" />%s</label></li>\n' \
                      % (aid, dsc))
    jotools.write(req, '</ul>\n')
    jotools.write(req, '<h2>%s</h2>' % _('Flags not set'))
    jotools.write(req, '<ul class="cblist">')
    for (aid, dsc) in flagattrs:
        jotools.write(req, '<li><label><input type="checkbox" name="flagoff%i" />%s</label></li>\n' \
                      % (aid, dsc))
    jotools.write(req, '</ul>\n')
    
    jotools.write(req, '<h2>%s</h2>\n<p>' % _('Output type'))
    for (tname, tdesc) in jooutput.list_supported_types():
        if tname == 'html': selected = 'checked="checked"'
        else: selected = ''
        jotools.write(req, ('<label><input type="radio" name="listtype" value="%s" %s />' +
                            '%s</label><br />\n') % (tname, selected, tdesc))
    jotools.write(req, '</p><p><input type="submit" value="%s" /><input type="reset" value="%s" /></p>\n' \
                  % (_('Search'), _('Reset')))
    jotools.write(req, '</form>\n')
    joheaders.page_footer_plain(req)
    return req.response()

@app.route('/query/wlist')
def query_wlist():
    req = jotools.Request_wrapper()
    # The select clause
    qselect = "SELECT w.wid, w.word, c.name AS classname, w.class FROM word w, wordclass c"

    # Initial conditions
    conditions = ["w.class = c.classid"]

    # Word form conditions
    word = jotools.get_param(req, 'word', '')
    if word != '':
        if not jotools.checkre(word):
            joheaders.error_page(req, _('Word has forbidden characters in it'))
            return "\n"
        if jotools.get_param(req, 'wordre', '') == 'on':
            try:
                re.compile(word)
            except re.error:
                joheaders.error_page(req, _('Search string is not a valid regular expression'))
                return "\n"
            compop = '~*'
            compword = jotools.expandre(word)
        elif jotools.get_param(req, 'wordsimplere', '') == 'on':
            compop = 'ILIKE'
            compword = word
        else:
            compop = '='
            compword = word
        # Use subquery if searching from alternative forms
        cond = "w.word %s '%s'" % (compop, jotools.escape_sql_string(compword))
        if jotools.get_param(req, 'altforms', '') == 'on':
            cond = cond + " OR w.wid IN (" + \
                   "SELECT rw.wid FROM related_word rw WHERE " + \
                   "replace(replace(rw.related_word, '=', ''), '|', '') %s '%s')" \
                   % (compop, jotools.escape_sql_string(compword))
        conditions.append(cond)
    
    # Word class conditions
    wclass = jotools.toint(jotools.get_param(req, 'wordclass', ''))
    if wclass > 0:
        conditions.append("w.class = %i" % wclass)
    
    # Text attribute conditions
    aid = jotools.toint(jotools.get_param(req, 'textaid', ''))
    if aid != 0:
        value = jotools.get_param(req, 'textvalue', '')
        if value == '':
            cond = "w.wid NOT IN (SELECT wid FROM string_attribute_value WHERE aid = %i)" % aid
        else:
            cond = ("w.wid IN (SELECT wid FROM string_attribute_value " +
                    "WHERE aid = %i AND value = '%s')") % (aid, jotools.escape_sql_string(value))
        conditions.append(cond)
    
    # Flag conditions
    for field in request.args.keys():
        if field.startswith('flagon'):
            aid = jotools.toint(field[6:])
            if jotools.get_param(req, 'flagon%i' % aid, '') == 'on':
                cond = "w.wid IN (SELECT wid FROM flag_attribute_value WHERE aid = %i)" % aid
                conditions.append(cond)
        if field.startswith('flagoff'):
            aid = jotools.toint(field[7:])
            if jotools.get_param(req, 'flagoff%i' % aid, '') == 'on':
                cond = "w.wid NOT IN (SELECT wid FROM flag_attribute_value WHERE aid = %i)" % aid
                conditions.append(cond)
    
    # FIXME: user should be able to select the order
    order = "ORDER BY w.word, c.name, w.wid"
    
    # Build the full select clause
    if len(conditions) == 0:
        select = qselect + " " + order
    elif len(conditions) == 1:
        select = qselect + " WHERE (" + conditions[0] + ") " + order
    else:
        select = qselect + " WHERE (" + conditions[0]
        for condition in conditions[1:]:
            select = select + ") AND (" + condition
        select = select + ") " + order
    
    outputtype = jotools.get_param(req, "listtype", 'html')
    jooutput.call(req, outputtype, select)
    return req.response()

@app.route('/query/listchanges', methods = ['GET'])
def listchanges():
    req = jotools.Request_wrapper()
    sdate = jotools.get_param(req, 'sdate', None)
    edate = jotools.get_param(req, 'edate', None)
    db = jodb.connect()
    (uid, uname, editable) = jotools.get_login_user(req)
    joheaders.page_header_navbar_level1(req, _('List changes'), uid, uname)
    
    edt = datetime.datetime.now()
    sdt = edt - datetime.timedelta(days=1)
    if sdate != None:
        try:
            stime = time.strptime(sdate, '%Y-%m-%d')
            sdt = datetime.datetime(*stime[0:5])
        except:
            jotools.write(req, "<p>%s</p>\n" % _("Invalid start date"))
    if edate != None:
        try:
            etime = time.strptime(edate, '%Y-%m-%d')
            edt = datetime.datetime(*etime[0:5])
        except:
            jotools.write(req, "<p>%s</p>\n" % _("Invalid end date"))
    sdate_s = sdt.strftime('%Y-%m-%d')
    edate_s = edt.strftime('%Y-%m-%d')
    
    jotools.write(req, """
<form method="get" action="listchanges">
<label>%s <input type="text" name="sdate" value="%s"/></label><br />
<label>%s <input type="text" name="edate" value="%s"/></label><br />
<input type="submit" /> <input type="reset" />
</form>
    """ % (_('Start date'), sdate_s, _('End date'), edate_s))
    
    # Increase edt by one day to make the the SQL between operator act on timestamps
    # in a more intuitive way.
    edt = edt + datetime.timedelta(days=1)
    edate_s = edt.strftime('%Y-%m-%d')
    
    results = db.query("""
    SELECT u.uname, to_char(w.ctime, 'YYYY-MM-DD HH24:MI:SS'),
           coalesce(u.firstname, ''), coalesce(u.lastname, ''),
           '%s', NULL, w.wid, w.word
    FROM word w, appuser u WHERE w.cuser = u.uid AND w.ctime BETWEEN '%s' AND '%s'
    UNION
    SELECT u.uname, to_char(e.etime, 'YYYY-MM-DD HH24:MI:SS'),
           coalesce(u.firstname, ''), coalesce(u.lastname, ''),
           e.message, e.comment, w.wid, w.word
    FROM appuser u, event e, word w WHERE u.uid = e.euser AND e.eword = w.wid
    AND e.etime BETWEEN '%s' AND '%s'
    ORDER BY 2 DESC""" % (_('Word created'), sdate_s, edate_s, sdate_s, edate_s));
    
    if results.ntuples() > 1000:
        jotools.write(req, '<p>%s</p>' % _('Too many changes, use narrower date interval.'))
        joheaders.page_footer_plain(req)
        return req.response()
    retstr = ''
    for result in results.getresult():
        wordlink = '<a href="../word/edit?wid=%i">%s</a>' \
                   % (result[6], jotools.escape_html(result[7]))
        date = result[1]
        user = jotools.escape_html(result[2]) + " " + \
               jotools.escape_html(result[3]) + " (" + \
               jotools.escape_html(result[0]) + ")"
        retstr = retstr + ('<div class="logitem"><p class="date">%s %s %s</p>\n' \
                           % (wordlink, user, date))
        if result[4] != None:
            msg = jotools.escape_html(result[4]).strip()
            msg = msg.replace('\n', '<br />\n')
            retstr = retstr + '<p class="logmsg">%s</p>\n' % msg
        if result[5] != None:
            comment = jotools.escape_html(result[5]).strip()
            comment = comment.replace('\n', '<br />\n')
            comment = jotools.comment_links(comment)
            retstr = retstr + '<p class="comment">%s</p>\n' % comment
        retstr = retstr + "</div>\n"
    
    jotools.write(req, retstr)
    joheaders.page_footer_plain(req)
    return req.response()

@app.route('/ehdotasanoja', methods = ['POST', 'GET'])
def ehdotasanoja():
    req = jotools.Request_wrapper()
    ehdotasanoja_index(req)
    return req.response()

@app.route('/findclass/classlist')
def findclass_classlist():
    req = jotools.Request_wrapper()
    classlist(req)
    return req.response()

@app.route('/user/login', methods = ['POST'])
def login():
    req = jotools.Request_wrapper()
    password = jotools.get_param(req, 'password', None)
    username = jotools.get_param(req, 'username', None)
    if username == None or password == None or not jotools.checkuname(username):
        joheaders.error_page(req,
                         _("Missing or incorrect username or password"))
        return req.response()
    
    pwhash = hashlib.sha1((_config.PW_SALT + password).encode('UTF-8')).hexdigest()
    db = jodb.connect_private()
    results = db.query(("select uid, isadmin from appuser where uname = $1 and pwhash = $2 and disabled = FALSE"), (username, pwhash))
    if results.ntuples() == 0:
        joheaders.error_page(req, _("Incorrect username or password"))
        return req.response()
    
    (uid, isadmin) = results.getresult()[0]
    if isadmin == 'f' and _config.ONLY_ADMIN_LOGIN_ALLOWED:
        joheaders.error_page(req, _("Only administrator logins are allowed at the moment"))
        return req.response()
    
    # Generate session key
    sesssha = hashlib.sha1()
    sesssha.update(username.encode('UTF-8'))
    sesssha.update(pwhash.encode('UTF-8'))
    sesssha.update(os.urandom(15))
    sesskey = sesssha.hexdigest()
    
    db.query(("update appuser set session_key = '%s', session_exp = CURRENT_TIMESTAMP + " +
              "interval '%i seconds' where uid = %i") % (sesskey, _config.SESSION_TIMEOUT, uid))
    if _config.WWW_ROOT_DIR == '': cookiepath = '/'
    else: cookiepath = _config.WWW_ROOT_DIR
    req.headers_out['Set-Cookie'] = 'session=%s; path=%s' % (sesskey, cookiepath)
    wid = jotools.get_param(req, 'wid', None)
    if wid == None: wid_n = 0
    else: wid_n = jotools.toint(wid)
    if wid_n != 0:
        joheaders.redirect_header(req, _config.WWW_ROOT_DIR + "/word/edit?wid=%i" % wid_n)
    elif jotools.get_param(req, 'redir', None) != None:
        joheaders.redirect_header(req, _config.WWW_ROOT_DIR +
                                       jotools.get_param(req, 'redir', ''))
    else: joheaders.redirect_header(req, _config.WWW_ROOT_DIR + "/")
    req.write('</html>')
    return req.response()

@app.route('/user/logout', methods = ['POST'])
def logout():
    req = jotools.Request_wrapper()
    session = jotools.get_session(req)
    if session != '':
        db = jodb.connect_private()
        db.query("update appuser set session_key = NULL, session_exp = NULL " +
                 "where session_key = $1", (session,))
    req.headers_out['Set-Cookie'] = 'session=; path=%s; expires=Thu, 01-Jan-1970 00:00:01 GMT' \
                                    % _config.WWW_ROOT_DIR
    wid = jotools.get_param(req, 'wid', None)
    if wid == None: wid_n = 0
    else: wid_n = jotools.toint(wid)
    if wid_n == 0: joheaders.redirect_header(req, _config.WWW_ROOT_DIR + "/")
    else: joheaders.redirect_header(req, _config.WWW_ROOT_DIR + "/word/edit?wid=%i" % wid_n)
    req.write('</html>')
    return req.response()

@app.route('/user/addform', methods = ['GET'])
def user_addform():
    req = jotools.Request_wrapper()
    (uid, uname, editable) = jotools.get_login_user(req)
    if not jotools.is_admin(uid):
        joheaders.error_page(req, _('You must be an administrator to do this'))
        return req.response()
    joheaders.page_header_navbar_level1(req, _('Add user'), uid, uname)
    jotools.write(req, '''
<form method="post" action="add">
<table>
<tr><td>%s</td><td><input type="text" name="firstname" /></td></tr>
<tr><td>%s</td><td><input type="text" name="lastname" /></td></tr>
<tr><td>%s</td><td><input type="text" name="uname" /></td></tr>
<tr><td>%s</td><td><input type="text" name="email" /></td></tr>
<tr><td>%s</td><td><input type="text" name="passwd" /></td></tr>
</table>
<input type="submit" value="%s" />
</form>
'''        % (_('First name'), _('Last name'), _('Username'), _('Email address'),
              _('Password'), _('Add user')))
    joheaders.page_footer_plain(req)
    return req.response()

@app.route('/user/add', methods = ['POST'])
def user_add():
    req = jotools.Request_wrapper()
    (uid, uname, editable) = jotools.get_login_user(req)
    if not jotools.is_admin(uid):
        joheaders.error_page(req, _('You must be an administrator to do this'))
        return req.response()
    datafields = ['firstname', 'lastname', 'uname', 'email', 'passwd']
    values = {}
    for datafield in datafields:
        values[datafield] = jotools.get_param(req, datafield, '')
        if datafield != 'passwd':
            values[datafield] = jotools.escape_sql_string(values[datafield])
        if datafield not in ['email', 'passwd'] and values[datafield] == '':
            joheaders.error_page(req, _('Required field %s is missing') % datafield)
            return req.response()
    if values['passwd'] == '':
        joheaders.error_page(req, _('Required field %s is missing') % 'passwd')
        return req.response()
    pwhash = hashlib.sha1((_config.PW_SALT + values['passwd']).encode('UTF-8')).hexdigest()
    privdb = jodb.connect_private()
    newuid = privdb.query("SELECT nextval('appuser_uid_seq')").getresult()[0][0]
    try:
        privdb.query(("INSERT INTO appuser(uid, uname, firstname, lastname, email, pwhash)" +
                      "VALUES(%i, '%s', '%s', '%s', '%s', '%s')") % (newuid, values['uname'],
                values['firstname'], values['lastname'], values['email'], pwhash))
    except ProgrammingError:
        joheaders.error_page(req, _('User name is already in use'))
        return req.response()
    db = jodb.connect()
    db.query(("INSERT INTO appuser(uid, uname, firstname, lastname, email)" +
              "VALUES(%i, '%s', '%s', '%s', '%s')") % (newuid, values['uname'],
        values['firstname'], values['lastname'], values['email']))
    joheaders.ok_page(req, _('New user was added succesfully'))
    return req.response()

@app.route('/user/passwdform', methods = ['GET'])
def user_passwdform():
    req = jotools.Request_wrapper()
    (uid, uname, editable) = jotools.get_login_user(req)
    if uid == None:
        joheaders.error_page(req, _('You must be logged in to do this'))
        return req.response()
    joheaders.page_header_navbar_level1(req, _('Change password'), uid, uname)
    jotools.write(req, '''
<form method="post" action="changepasswd">
<table>
<tr><td>%s</td><td><input type="password" name="oldpw" /></td></tr>
<tr><td>%s</td><td><input type="password" name="newpw" /></td></tr>
</table>
<input type="submit" value="%s" />
</form>
'''        % (_('Old password'), _('New password'), _('Change password')))
    joheaders.page_footer_plain(req)
    return req.response()

@app.route('/user/changepasswd', methods = ['POST'])
def user_changepasswd():
    req = jotools.Request_wrapper()
    (uid, uname, editable) = jotools.get_login_user(req)
    if uid == None:
        joheaders.error_page(req, _('You must be logged in to do this'))
        return req.response()
    oldpw = jotools.get_param(req, 'oldpw', '')
    newpw = jotools.get_param(req, 'newpw', '')
    if oldpw == '' or newpw == '':
        joheaders.error_page(req, _('Required field is missing'))
        return req.response()
    oldpwhash = hashlib.sha1((_config.PW_SALT + oldpw).encode('UTF-8')).hexdigest()
    db = jodb.connect_private()
    results = db.query(("select uid from appuser where uid = %i and pwhash = '%s'") \
                       % (uid, oldpwhash))
    if results.ntuples() == 0:
        joheaders.error_page(req, _("Incorrect old password"))
        return req.response()
    newpwhash = hashlib.sha1((_config.PW_SALT + newpw).encode('UTF-8')).hexdigest()
    db.query("update appuser set pwhash = '%s' where uid = %i" % (newpwhash, uid))
    joheaders.ok_page(req, _('Password was changed succesfully'))
    return req.response()

@app.route('/jscripts.js')
def scripts():
    return send_file('jscripts.js')

@app.route('/style.css')
def style():
    return send_file('style.css')
