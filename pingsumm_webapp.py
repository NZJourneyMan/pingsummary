#!/usr/bin/env python3

import os
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.png', mimetype='image/vnd.microsoft.icon')

# Index handling
@app.route('/')
def index(methods=['GET']):
    return render_template('ping_summary.html')

# Boiler plate pages for 500, 404 and testing 500
@app.errorhandler(404)
def do404(e):
    return render_template('message.html',
                           msg='Sorry, but that page doesn\'t exist<br>(404)',
                           but='Ok'), 404


@app.errorhandler(500)
def do500(e):
    return render_template('message.html',
                           msg='Oops, something blew up!<br>(500)',
                           but='Ok'), 500


if __name__ == '__main__':
    # app.debug = True
    app.run(host='0.0.0.0', port=2233)
