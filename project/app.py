import os

from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename

from bs4 import BeautifulSoup
import re

from .counter import start, make_table, get_cmmts, Comment, SubTheme

from flask_bootstrap import Bootstrap

import jsonpickle
from flask import g

#global vars
app = Flask(__name__)  
Bootstrap(app)

app.secret_key = 'sads9f8b378asbfas9ah'
app.config['UPLOAD_PATH'] = './uploads'


@app.route("/", methods=["POST"])
def upload():

    if request.form.get('submit_t') =="enter":
        processed_text = request.form['text']
        print(processed_text)
        try:
            session['thresh_val'] = float(processed_text)
        except:
            session['thresh_val'] = .65
        return render_template('index.html',t_val = session['thresh_val'])
    elif request.form.get('submit_f') =="Submit Files":
        if 'thresh_val' not in session:
            session['thresh_val'] = .65

        g.theme_dict = dict()
        g.main_theme_list = []
        g.sub_code_list = []
        uploaded_files = request.files.getlist("file[]")
        print (uploaded_files)

        result_list = start(uploaded_files,session['thresh_val'])
        table_html = make_table(result_list)

        return render_template('index.html', table = table_html, t_val = session['thresh_val'])

@app.route('/')
def my_form():
    session.clear()
    print("sleared session")

    try:
        return render_template('index.html',t_val = session['thresh_val'] )
    except:
        session['thresh_val'] = .65
        return render_template('index.html',t_val = .65 )


if __name__ == '__main__':
    app.run()