from bs4 import BeautifulSoup
import re
from difflib import SequenceMatcher as SM
from nltk.util import ngrams
import codecs

from flask_table import Table, Col
from flask import Flask, request, render_template, redirect, url_for, session
import flask
import csv
import os.path

from w3lib.html import replace_entities

#global vars
# theme_dict = dict()
main_theme_list = []
soup =  BeautifulSoup(features="html.parser")
sub_code_list = []
# sim_value = .50

class Comment:
    def __init__(self, comment, file_name):
        self.file_name = file_name
        self.comment = comment

    def __eq__(self, other):
        if isinstance(other, Comment):
            return self.comment.lower() == other.comment.lower()
        return False

class SubTheme:
    def __init__(self, theme):
        self.theme = theme
        self.comments = []
    
    def add_cmmts(self, text, file_name):
        self.comments.append(Comment(text,file_name))

    def __eq__(self, other):
        if isinstance(other, SubTheme):
            return self.theme.lower() == other.theme.lower()
        return False

def add_code_from_txt():
    # global theme_dict
    theme_dict = session['theme_dict']
    my_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(my_path, "../project/code_chart.txt")

    f = open(path,'r')
    curr_main_theme = ""
    for line in f:
        text = line.strip()
        if(text[0] == "*"):
            #adds to main_theme_list (raw)
            main_theme_list.append(text[1:])
            single_theme = text.split('|')[0][1:]
            curr_main_theme = single_theme
            #initalizes dict key
            theme_dict[single_theme] = []
        else:
            single_sub_theme = text.split('|')[0]
            #adds to sub_code_list (raw)
            sub_code_list.append(text)

            theme_dict[curr_main_theme].append(SubTheme(single_sub_theme))


def store_data(file_in, sim_value_in):
    global soup
    theme_dict = session['theme_dict']
    soup = BeautifulSoup(file_in, "html.parser")
    # for cmmt in soup.find_all('span', {'class' : 'c2'}):
    all_cmmts = soup.find_all("a", href=re.compile("cmnt_"))
    for cmmt in all_cmmts:
        ref_num_indx = str(cmmt['href']).find('ref')
        ref_num = str(cmmt['href'])[ref_num_indx+3:]
        comment_link = soup.find("a", href=re.compile("#cmnt"+str(ref_num)))
        try:
            original_text_list = comment_link.parent.parent.find_all("span")
            single_orig_text = ""
            for curr_text in original_text_list:
                single_orig_text +=  "\n" + curr_text.text
            # print(single_orig_text)
        except:
            single_orig_text = "None"
        # print ("Found the URL:", cmmt['href'])
        parent_of_cmmt = cmmt.parent.parent
        comments = parent_of_cmmt.find_all("span")

        for comment in comments:
            if comment.text.replace(" ", "") == "":
                continue
            comment_sub_list = []
            # splitter
            mod_comment = comment.text.replace("and","/")
            index_slash = mod_comment.find("/")
            if index_slash > 0:
                comment_sub_list.append(mod_comment[0:index_slash])
                comment_sub_list.append(mod_comment[index_slash+1:])
            else:
                comment_sub_list.append(mod_comment)

            #sets main theme
            main_theme = fuzzy_best_match(comment_sub_list[0], main_theme_list, sim_value_in)

            for formated_comment in comment_sub_list:
                # main_theme = fuzzy_best_match(formated_comment, main_theme_list)
                sub_theme = fuzzy_best_match(formated_comment, sub_code_list, sim_value_in)
                
                #checks if the sub theme already exists
                sub_theme_in_list = False 
                for key, value in theme_dict.items():
                    for value_sub_theme in value:
                        if SubTheme(sub_theme) == value_sub_theme:
                            main_theme = key
                            sub_theme_in_list = True

                if sub_theme_in_list == False:    
                    #checks if the main theme already exists
                    theme_in_list = False
                    for key, value in theme_dict.items():
                        if main_theme == key:
                            theme_in_list = True
                    
                    if theme_in_list == False:
                        theme_dict[main_theme] = []  
                    
                    #adds the appropriate 
                    theme_dict[main_theme].append(SubTheme(sub_theme))

                index_of_curr = theme_dict[main_theme].index(SubTheme(sub_theme))
                # print(formated_comment)
                # print(replace_entities(single_orig_text))
                theme_dict[main_theme][index_of_curr].add_cmmts(replace_entities(single_orig_text),file_in.filename)

def fuzzy_best_match(cmmt, list_in, sim_value_in):
    sim_value = sim_value_in
    largest_sim_val = 0
    best_match = ""
    for code in list_in:
        curr_sim_val = fuzzy_finder(code, cmmt)
        if curr_sim_val > largest_sim_val:
            largest_sim_val = curr_sim_val
            best_match = str(code)
    best_match_list = best_match.split('|')
    if largest_sim_val >= sim_value:
        return best_match_list[0]
    else:
        return cmmt


def fuzzy_finder(needle_in, hay_in):
    needle = needle_in
    hay = hay_in
    needles = needle.split('|')
    
    overall_max_sim_val = 0
    for nddle in needles:
        needle_length  = len(nddle.split())
        max_sim_val    = 0
        max_sim_string = u""

        for ngram in ngrams(hay.split(), needle_length + int(.2*needle_length)):
            hay_ngram = u" ".join(ngram)
            similarity = SM(None, hay_ngram, nddle).ratio() 
            if similarity > max_sim_val:
                max_sim_val = similarity
                max_sim_string = hay_ngram

                if max_sim_val >= overall_max_sim_val:
                    overall_max_sim_val = max_sim_val
    return max_sim_val

def calculate_data():
    for key, value in theme_dict.items():
        print("________________"+ key + "__________________")
        for indv_theme in value:
            print(str(indv_theme.theme) + " ~~ "+ str(len(indv_theme.comments)))      
        print("")


def start(files_in, thresh_val):
    # global theme_dict
    # global sim_value
    initialized = False

    sim_value = thresh_val

    for curr_file in files_in:
        if initialized == False:
            add_code_from_txt()
        store_data(curr_file, sim_value)
        initialized = True
    # print("from start: "+ str(len(session['theme_dict'])))
    # print("TYPE OF THEME_DICT = " + str(type(session['theme_dict'])))
    return session['theme_dict']
    # calculate_data()
    # make_table()

class ItemTable(Table):
   m_theme = Col('Main Theme')
   sub_theme = Col('Sub Theme')
   count = Col('Count')
   btn = Col('Comments')
#    list_of_cmmts = Col('Comments')

# Get some objects
class Item(object):
    def __init__(self, m_theme, sub_theme,count, list_of_cmmts, btn):
        self.m_theme = m_theme
        self.sub_theme = sub_theme
        self.count = count
        self.list_of_cmmts = list_of_cmmts
        self.btn = btn

def make_table():
    items = []
    theme_dict = session['theme_dict']
    for key, value in theme_dict.items():
        for sub_theme in value:
            items.append(Item(key, sub_theme.theme, len(sub_theme.comments), sub_theme.comments, '<form method="post"><input action="/" type="submit" value="'+sub_theme.theme+'" name="btn_cmmt" style="color:#3498DB;background-color:#3498DB;width:56px;height=50px;height:20px;"/></form>'))
            
    # Populate the table
    table = ItemTable(items)

    table_html = str(table.__html__()).replace("<table>",'<table class="table">')
    table_html = replace_entities(table_html)
    # print("from make table method"+ str(len(theme_dict)))
    # print(table_html)
    return table_html
    # or just {{ table }} from within a Jinja template

def get_cmmts(sub_theme_in):
    theme_dict = session['theme_dict']
    # print(len(theme_dict))
    for key, value in theme_dict.items():
        for sub_theme in value:
            if(sub_theme == SubTheme(sub_theme_in)):
                return sub_theme.comments
    # print("NO COM MENT LIST IN " + sub_theme_in)
    return []
            #make else here