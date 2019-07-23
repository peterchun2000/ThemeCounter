import os

from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename

from bs4 import BeautifulSoup
import re

from counter import start, make_table

from flask_bootstrap import Bootstrap

#global vars
app = Flask(__name__)  
Bootstrap(app)

app.config['UPLOAD_PATH'] = './uploads'
thresh_val = 0.65
@app.route("/", methods=["POST"])
def upload():
    global thresh_val
    if request.form.get('submit_t') =="enter":
        processed_text = request.form['text']
        print(processed_text)
        try:
            thresh_val = float(processed_text)
        except:
            thresh_val = .65
        return render_template('index.html',t_val = thresh_val)
    else:
        uploaded_files = request.files.getlist("file[]")
        print (uploaded_files)
        print(thresh_val)
        start(uploaded_files,thresh_val)
        return make_table()

@app.route('/')
def my_form():
    return render_template('index.html',t_val = thresh_val)