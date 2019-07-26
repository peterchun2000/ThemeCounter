import os

from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename

from bs4 import BeautifulSoup
import re

from counter import start, make_table, get_cmmts

from flask_bootstrap import Bootstrap

#global vars
app = Flask(__name__)  
Bootstrap(app)

app.secret_key = 'sads9f8b378asbfas9ah'
app.config['UPLOAD_PATH'] = './uploads'
# thresh_val = 0.65

@app.route("/", methods=["POST"])
def upload():
    # thresh_val = .65
    if request.form.get('submit_t') =="enter":
        processed_text = request.form['text']
        print(processed_text)
        try:
            session['thresh_val'] = float(processed_text)
        except:
            session['thresh_val'] = .65
        return render_template('index.html',t_val = session['thresh_val'])
    elif request.form.get('submit_f') =="Submit Files":
        uploaded_files = request.files.getlist("file[]")
        print (uploaded_files)
        print(session['thresh_val'])
        results = start(uploaded_files,session['thresh_val'])
        print(results)
        html_table = make_table()
        return render_template('index.html', table = html_table, t_val = session['thresh_val'])
        
    else:
        print("from main" + str(len(session['theme_dict'])))
        return render_template('comment.html', comments = get_cmmts(request.form.get('btn_cmmt')))

@app.route('/')
def my_form():
    try:
        len(session['theme_dict'])
    except:
        session['theme_dict'] = dict()

    # global thresh_val
    try:
        return render_template('index.html',t_val = session['thresh_val'] )
    except:
        return render_template('index.html',t_val = .64 )


if __name__ == '__main__':
    app.run()