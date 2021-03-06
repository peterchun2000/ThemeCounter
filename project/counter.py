from bs4 import BeautifulSoup
import re
from difflib import SequenceMatcher as SM
from nltk.util import ngrams
import codecs

from flask_table import Table, Col
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import csv
import os.path

from w3lib.html import replace_entities

import jsonpickle
from flask import g

from itertools import count
import re

#global vars
soup =  BeautifulSoup(features="html.parser")

class Comment:
    def __init__(self, comment, file_name):
        self.file_name = file_name
        self.comment = comment

    def __eq__(self, other):
        if isinstance(other, Comment):
            return self.comment == other.comment
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
    # print("theme dict length from start: " + str(len(session['theme_dict'])))
    theme_dict =dict()
    # print("theme dict length from start: " + str(len(session['theme_dict'])))
    sub_code_list = g.sub_code_list
    my_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(my_path, "../project/code_chart.txt")
    main_theme_list =  g.main_theme_list
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
    return theme_dict


def store_data(file_in, sim_value_in, initialized_list):
    global soup
    main_theme_list = g.main_theme_list
    sub_code_list = g.sub_code_list

    theme_dict = initialized_list

    soup = BeautifulSoup(file_in, "html.parser")

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

        except:
            print("bad")
        parent_of_cmmt = cmmt.parent.parent
        comments = parent_of_cmmt.find_all("span")
        for comment in comments:
            if comment.text.replace(" ", "") == "" or comment.text[0]=="[":
                print("contineudasdf")
                continue
            comment_sub_list = []
            # splitter
            index_of_coln = comment.text.find(":")
            mod_comment = comment.text.replace("and","/")
            index_slash = mod_comment.find("/")
            if index_slash > 0:
                comment_sub_list.append(mod_comment[index_of_coln+1:index_slash])
                comment_sub_list.append(mod_comment[index_slash+1:])
            else:
                if index_of_coln != -1:
                    comment_sub_list.append(mod_comment[index_of_coln+1:])
                else:
                    comment_sub_list.append(mod_comment)
            
            #sets main theme
            if index_of_coln != -1:
                main_theme = fuzzy_best_match(comment.text[0:index_of_coln], main_theme_list, sim_value_in)
            else:
                # print(comment.text)
                main_theme = fuzzy_best_match(comment.text, main_theme_list, sim_value_in-.05)

            for formated_comment in comment_sub_list:
                # main_theme = fuzzy_best_match(formated_comment, main_theme_list)
                # print(formated_comment)
                sub_theme = fuzzy_best_match(formated_comment, sub_code_list, sim_value_in)
                if sub_theme.replace(" ","") == "":
                    continue
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

                theme_dict[main_theme][index_of_curr].add_cmmts(replace_entities(single_orig_text),file_in.filename)
    return theme_dict

def fuzzy_best_match(cmmt, list_in, sim_value_in):
    sim_value = sim_value_in
    largest_sim_val = 0

    best_match = ""
    for code in list_in:
        single_code = code.split('|')[0]
        if single_code.lower().replace(' ','') == cmmt[0:].lower().replace(' ',''):
            return str(single_code)
        curr_sim_val = fuzzy_finder(code, cmmt)
        if curr_sim_val > largest_sim_val:
            largest_sim_val = curr_sim_val
            best_match = str(single_code)
    
    if largest_sim_val >= sim_value:
        return best_match
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

                if max_sim_val > overall_max_sim_val:
                    overall_max_sim_val = max_sim_val
    return overall_max_sim_val

def start(files_in, thresh_val):
    initialized = False

    sim_value = thresh_val

    for curr_file in files_in:
        if initialized == False:
            initialized_list=add_code_from_txt()
        result_list = store_data(curr_file, sim_value,initialized_list )
        initialized = True

    return result_list

# for the table
class ItemTable(Table):
    m_theme = Col('Main Theme')
    sub_theme = Col('Sub Theme')
    count = Col('Count')
    bttn = Col('')

# Get some objects
class Item(object):
    def __init__(self, m_theme, sub_theme,count, list_of_cmmts, bttn):
        self.m_theme = m_theme
        self.sub_theme = sub_theme
        self.count = count
        self.list_of_cmmts = list_of_cmmts
        self.bttn = bttn

def make_table(result_list):
    items = []
    theme_dict = result_list

    for key, value in theme_dict.items():
        for sub_theme in value:
            items.append(Item(key, sub_theme.theme, len(sub_theme.comments), sub_theme.comments, '<button type="button" data-toggle="collapse" data-target="#demo" class="accordion-toggle btn btn-default">Comments</button>'))
              
    # Populate the table
    table = ItemTable(items)

    table_html = str(table.__html__().replace("<table>",'<table class="table">'))
    # print(table_html)
    table_html = replace_entities(table_html)

    counter1 = count(1)
    table_html = re.sub('data-target="#demo', lambda m: m.group() + str(next(counter1)), table_html)
    
    table_html = table_html.replace("</td></tr>", '</td></tr> <tr> <td colspan="6" class="hiddenRow"style="padding:0!important;"><div class="accordian-body collapse" id="demo"> <ul class="list-group"> [cmmt] </ul> </div></td></tr>')
    counter2 = count(1)
    table_html = re.sub('id="demo', lambda m: m.group() + str(next(counter2)), table_html)
    for key, value in theme_dict.items():
        for sub_theme in value:
            table_html = table_html.replace('[cmmt]', get_cmmts(sub_theme.theme, theme_dict),1)
    g.theme_dict = result_list

    return table_html

def get_cmmts(sub_theme_in, theme_dict_in):
    theme_dict = theme_dict_in

    result_str = ""
    for key, value in theme_dict.items():
        for sub_theme in value:
            if(sub_theme == SubTheme(sub_theme_in)):
                for ind_cmmt in sub_theme.comments:
    
                    result_str += '<li class="list-group-item">'+'<b>' + ind_cmmt.file_name + '</b>' + '<br>' + ind_cmmt.comment+"</li>"
    return result_str


def get_subtheme_list():
    theme_dict = g.theme_dict 
    result_list = []

    for key, value in theme_dict.items():
        for sub_theme in value:
            if(sub_theme == SubTheme(sub_theme_in)):
                return sub_theme.comments
    return []

