#!/usr/bin/env python3

# innogy - fetch account balances from Innogy Poland (utility company)
# Copyright (C) 2016 Maciej Grela <enki@fsck.pl>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import requests
import logging
import re
import sqlite3
import urllib.parse
from optparse import OptionParser
from bs4 import BeautifulSoup

# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.

# *Uncomment this and set the log level in basicConfig to DEBUG in order to enable debugging of HTTP requests/responses*
# try:
#     import http.client as http_client
# except ImportError:
#     # Python 2
#     import httplib as http_client
# http_client.HTTPConnection.debuglevel = 1

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

# *Uncomment this and set the log level in basicConfig to DEBUG in order to enable debugging of HTTP requests/responses*
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

#
# Parse command line options
#

parser = OptionParser()
parser.add_option('-l', '--login', dest='login', help='Use LOGIN as the login name', metavar='LOGIN')
parser.add_option('-d', '--db', dest='db_filename', help='Use DB as the sqlite database file', metavar='DB')
parser.add_option('-p', '--passwd-file', dest='password_file', help='Use PASSWORD_FILE to read the password', metavar='PASSWORD_FILE')

(options, args) = parser.parse_args()

login = options.login
if login is None:
    log.fatal("A login is required")

if options.password_file is not None:
    password = open(options.password_file, "rb").read().strip()

db = sqlite3.connect(options.db_filename)


class SessionWithUrlBase(requests.Session):
    # In Python 3 you could place `url_base` after `*args`, but not in Python 2.
    def __init__(self, url_base=None, *args, **kwargs):
        super(SessionWithUrlBase, self).__init__(*args, **kwargs)
        self.url_base = url_base

    def request(self, method, url, **kwargs):
        return super(SessionWithUrlBase, self).request(method, urllib.parse.urljoin(self.url_base, url), **kwargs)


s = SessionWithUrlBase(url_base='https://moje.innogy.pl/')
r = s.get("/Logowanie")

bs = BeautifulSoup(r.text, "lxml")
login_form = bs.find('form', action='/Logowanie')

if login_form is None:
    log.fatal("Could not find login form, response text is '%s'" % (r.text))

csrf_token = login_form.find('input', attrs={'name': '__RequestVerificationToken'})['value']
log.debug("CSRF token is '%s'" % (csrf_token))

log.info("Authenticating to '%s' as user '%s'" % (s.url_base, login))
r = s.post(login_form['action'], data={"UserName": login, "Password": password, '__RequestVerificationToken': csrf_token})
log.debug(r.text)

# Get our PH number (Partner Handlowy)
r = s.get("/Dane-i-ustawienia/Dane-Klienta")

bs = BeautifulSoup(r.text, 'lxml')
log.debug(bs)
cud = bs.find('span', class_='cud-value').get_text(strip=True)

log.debug("User '%s' has CUD identifier '%s'" % (login, cud))

r = s.get("/")
bs = BeautifulSoup(r.text, 'lxml')
for balance_span in bs.find_all('span', class_='balance-value'):
    id = balance_span['data-id']
    balance_url = balance_span['data-url']

    r = s.post(balance_url, data={'kuId': id})
    balance = r.json()
    if balance['Status'] != 1:
        log.error("Fetching balance for contract '%s' using '%s' failed, response text: '%s'" % (id, balance_url, r.text))
        continue

    balance_amount = re.match("([-0-9,]+) zł", balance['Message']).group(1).replace(',', '.')

    log.debug("CUD='%s' KU='%s' has amount '%s'" % (cud, id, balance_amount))

    try:
        data = {
            'cud_id': cud,
            'ku_id': id,
            'balance': balance_amount
        }

        db.execute("insert into innogy_data(ts, cud_id, ku_id, balance) values(datetime('now'), :cud_id, :ku_id, :balance)", data)
        db.commit()

    except Exception as e:
        log.fatal("Could not insert dataplan offer record with data '%s'" % (data))
        log.exception(e)


log.info("Logging out user '%s' from '%s'" % (login, s.url_base))
r = s.post('/api/sitecore/Account/LogOutUser')
