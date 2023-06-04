from flask import Flask, Response
import jodb
import jotools
import joheaders
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

@app.route('/word')
def word():
    return Response("<span style='color:red'>Joukahaista päivitetään, ja se palaa käyttöön kesän 2023 aikana.</span>", status=503)
