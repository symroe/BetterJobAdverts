import requests
import os
import json
from flask import request, render_template, send_from_directory
from bs4 import BeautifulSoup
from jobcert import app
import job_posting
from parser import Parser

@app.route('/')
def index():
    return render_template('index.html', menu_item="tools")

@app.route('/report')
def report():
    return render_template('report.html', menu_item="report")

@app.route('/api')
def api():
    return render_template('api.html', menu_item="api")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/check', methods=['GET', 'POST'])
def check():

    #get html
    error = False
    html = None
    url = None
    if request.method == 'POST':
        html = request.values['html']

    if request.method == 'GET':
        url = request.values['url']
        try:
            html = requests.get(url, verify=False).content
        except requests.exceptions.ConnectionError:
            error = "Sorry, that URL does not exist"
        except requests.exceptions.MissingSchema:
            error = "Sorry, that is not a valid URL"            
        except requests.exceptions.HTTPError:
            error = "Sorry, something went wrong"
        except requests.exceptions.Timeout:
            error = "Sorry, there was a timeout when trying to visit that URL"

    #parse
    parser = Parser()
    if error == False:
        parser.parse(html)

    return render_template('check.html', menu_item="tools", parser=parser, error=error, url=url)