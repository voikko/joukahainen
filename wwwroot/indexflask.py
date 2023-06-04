from flask import Flask, request, Response, send_file
import jodb
import jotools
import joheaders
import jooutput
import re
import _config

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
    results = db.query("select word, class from word where wid = %i" % wid_n)
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

@app.route('/jscripts.js')
def scripts():
    return send_file('jscripts.js')

@app.route('/style.css')
def style():
    return send_file('style.css')
