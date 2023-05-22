from flask import Flask, Response

app = Flask(__name__)

@app.route('/')
def index():
    return Response("<span style='color:red'>Joukahaista päivitetään, ja se palaa käyttöön toukokuun 2023 loppuun mennessä.</span>", status=503)
