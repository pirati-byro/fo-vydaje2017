#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''vysledky.py

Vypreparování dat z žádostí o proplacení za rok 2017

Plán:

1) Stáhni webovou stránku
2) Vysosej z ní metadata a zapiš je to tabulky v pandas
3) Ulož soubory do adresáře
4) Vyexportuj soubory v csv
'''

import time

start = time.time()

import requests
import pandas as pd
import numpy as np
pd.options.display.float_format = '{:.0f}'.format
from bs4 import BeautifulSoup
import os.path
import wget
from weasyprint import HTML
import csv
import logging

logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)


fileHandler = logging.FileHandler("{0}/{1}.log".format('.', 'report'))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


cwd = os.getcwd()

# configuration


#rozpočtová položka - kód, orgán, skladba, středisko, odkaz pdf, redmine žádost

vydaje = pd.DataFrame(columns=['značka', 'středisko', 'položka', 'částka','podáno', 'proplaceno', 'redmine', 'popis'])

def make_url(no):
    return 'https://wiki.pirati.cz/fo/vydaje/fo_' + str(no) + '_2017'

def print_time():
    global start
    end = time.time()
    logging.info('Skript běží: {0:.2f} sekund. '.format(end - start))

def parse_request(no):
    '''Stáhni žádost o proplacení s pořadovým číslem no v roce 2017'''
    global vydaje

    logging.info('Procesuje se žádost o proplacení FO '+str(no)+'/2017')

    link = make_url(no)+'?do=export_html'

    no_string= "{0:0>3}".format(no)

    mydir = 'output/' + no_string + '/'
    os.makedirs(mydir, exist_ok=True)

    # ulož txt

    downloaded_html=mydir+'zadost.html'

    if not os.path.isfile(downloaded_html):

        page = requests.get(link,verify=False)
        if page.status_code != requests.codes.ok:
            return 'Požadovaná žádost nenalezena'
        soup = BeautifulSoup(page.content, 'html.parser')
        soup.head.clear()
        with open(downloaded_html, "w") as file:
            file.write(soup.prettify())
        HTML(downloaded_html).write_pdf(mydir + 'zadost.pdf', stylesheets={'dokuwiki.css'})

    else:
        soup = BeautifulSoup(open(downloaded_html), 'html.parser')
        if not os.path.isfile(mydir + 'zadost.pdf'):
            soup.head.clear()
            HTML(downloaded_html).write_pdf(mydir+'zadost.pdf', stylesheets={'dokuwiki.css'})

    # definiční seznam v html
    dl= soup.find_all('div', class_='dataplugin_entry')[0].dl

    try:
        znacka=dl.find_all('dd', class_='značka')[0].get_text().strip()
    except Exception:
        logging.warning('Nepodařilo se najít značku')

    try:
        slozka=dl.find_all('dd', class_='složka')[0].a.get_text().strip()
    except Exception:
        logging.warning('Nepodařilo se najít složku')
        slozka = ''

    try:
        polozka_url=dl.find_all('dd', class_='položka')[0].a['href'].strip().split('/')
        polozka = polozka_url[-1]
        stredisko = polozka_url[-2]
    except Exception:
        logging.warning('Nepodařilo se najít položku')
        polozka = np.nan
        stredisko = np.nan

    try:
        nazev=dl.find_all('dd', class_='název')[0].get_text().strip()
    except Exception:
        logging.warning('Nepodařilo se najít název')
        nazev=''

    try:
        castka=dl.find_all('dd', class_='částka')[0].get_text().strip()
    except Exception:
        logging.warning('Nepodařilo se najít částku')
        castka=np.nan

    try:
        a_doklady = dl.find_all('dd', class_='doklad')[0].find_all('a')
    except Exception:
        logging.warning('Nepodařilo se najít doklady')
        a_doklady = []

    try:
        podano=dl.find_all('dd', class_='podáno')[0].get_text().strip()
    except Exception:
        logging.warning('Nepodařilo se najít datum podání')
        podano = ''

    try:
        proplaceno = dl.find_all('dd', class_='proplaceno')[0].get_text().strip()
    except Exception:
        logging.warning('Nepodařilo se najít datum proplacení')
        proplaceno = ''


    # uložení dokladů
    doklad_no = 0
    for a_doklad in a_doklady:
        doklad_no=doklad_no+1

        odkaz=a_doklad['href']
        if odkaz[0]=='/':
            odkaz='http://wiki.pirati.cz'+odkaz
        extension=os.path.splitext(odkaz)[1]

        downloaded_doklad_file = mydir + 'doklad' + str(doklad_no) + extension
        if not os.path.isfile(downloaded_doklad_file):
            try:
                wget.download(odkaz, downloaded_doklad_file)
            except Exception:
                logging.warning('Nepodařilo se stáhnout soubor '+odkaz)


    # hledání příslušného úkolu v redmine

    redmine_url= 'https://redmine.pirati.cz/projects/fo/issues.csv?c%5B%5D=subject&c%5B%5D=assigned_to&c%5B%5D=status&c%5B%5D=priority&f%5B%5D=subject&f%5B%5D=&group_by=&op%5Bsubject%5D=%7E&set_filter=1&t%5B%5D=&utf8=%E2%9C%93&v%5Bsubject%5D%5B%5D=FO+'+str(no)+'%2F2017'

    redmine_local_url = mydir + 'redmine_tasks.csv'

    if not os.path.isfile(redmine_local_url):
        wget.download(redmine_url, redmine_local_url)

    the_file = open(redmine_local_url, 'r')
    reader = csv.reader(the_file)

    redmine_id = ''

    for i, row in enumerate(reader):
        if i == 1:
            redmine_id=row[0]
            redmine_id='https://redmine.pirati.cz/issues/'+redmine_id
            if not os.path.isfile(mydir + 'redmine_task.pdf'):
                wget.download(redmine_id+'.pdf', mydir + 'redmine_task.pdf')
            break

    # konečné přiřazení

    newline = {
                'značka': znacka,
                'položka': polozka,
                'středisko': stredisko,
                'částka': castka,
                'popis': nazev.replace('"',''),
                'podáno': podano,
                'proplaceno': proplaceno,
                'redmine': redmine_id
    }
    logging.info(newline)
    vydaje = vydaje.append(newline, ignore_index=True)
    print_time()

for no in range(1,420):
    parse_request(no)
    vydaje.to_csv('vydaje.csv',sep=';')

