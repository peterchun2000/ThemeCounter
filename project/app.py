import os

from flask import Flask, request, render_template, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename

from bs4 import BeautifulSoup
import re

from .counter import start, make_table, get_cmmts, Comment, SubTheme

from flask_bootstrap import Bootstrap

import jsonpickle
from flask import g

import keyring

#global vars
app = Flask(__name__)  
Bootstrap(app)

is_prod = os.environ.get('IS_HEROKU', None)

if is_prod:
    auth_pass = os.environ.get('auth_pass')
else:
    auth_pass = "asdf1234"

app.secret_key = 'sads9f8b378asbfas9ah'
app.config['UPLOAD_PATH'] = '../project'

ALLOWED_EXTENSIONS = set(['txt'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/download')
def downloadFile ():
    #For windows you need to use drive name [ex: F:/Example.pdf]
    path = "../project/code_chart.txt"
    return send_file(path, as_attachment=True)

@app.route('/codebook-rules')
def sendRules ():
    return render_template('rules.html')

@app.route("/", methods=["POST"])
def upload():
    if request.form.get('submit_chart') =="Submit File":
        # check if the post request has the file part
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            print('No file selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # if os.path.exists('../project/code_chart.txt'):
            #     os.remove('../project/code_chart.txt')
            filename = "code_chart.txt"
            my_path = os.path.abspath(os.path.dirname(__file__))
            rel_path = os.path.join(my_path, app.config['UPLOAD_PATH'])
            file.save(os.path.join(rel_path, filename))
            print('File successfully uploaded')
            return redirect('/')
        else:
            print('Allowed file type is txt')
            return redirect(request.url)

    if request.form.get('submit_t') =="enter":
        processed_text = request.form['text']
        print(processed_text)
        try:
            session['thresh_val'] = float(processed_text)
            if session['thresh_val'] > 1:
                session['thresh_val'] = 1.0
        except:
            session['thresh_val'] = .65
        return render_template('index.html',t_val = session['thresh_val'], auth_code = auth_pass)
    elif request.form.get('submit_f') =="Submit Files":
        if 'thresh_val' not in session:
            session['thresh_val'] = .65

        g.theme_dict = dict()
        g.main_theme_list = []
        g.sub_code_list = []
        uploaded_files = request.files.getlist("file[]")
        print (uploaded_files)
        try:
            result_list = start(uploaded_files,session['thresh_val'])
            table_html = make_table(result_list)
            return render_template('index.html', table = table_html, t_val = session['thresh_val'], auth_code = auth_pass)
        except:
            return render_template('index.html', table = "error, prob a bad codebook", t_val = session['thresh_val'], auth_code = auth_pass)

@app.route('/')
def my_form():
    session.clear()
    print("sleared session")
    try:
        return render_template('index.html',t_val = session['thresh_val'], auth_code = auth_pass)
    except:
        session['thresh_val'] = .65
        return render_template('index.html',t_val = .65, auth_code =auth_pass )


if __name__ == '__main__':
    app.run()