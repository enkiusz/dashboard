#!/usr/bin/env python3

# wiglestats - User stats fetcher
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

from bs4 import BeautifulSoup
import asciitable, sqlite3, logging
import requests, sys, os, getpass, time, json, logging

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
log = logging.getLogger(__name__)

# *Uncomment this and set the log level in basicConfig to DEBUG in order to enable debugging of HTTP requests/responses*
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

from optparse import OptionParser
from urllib.parse import urljoin

#
# Default configuration
#
origin = 'https://wigle.net/'
base_url = 'https://api.wigle.net/'
login = None

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
    log.error('A wigle.net login is required')
    sys.exit(1)

if options.password_file is not None:
    password = open(options.password_file, "rb").read().strip()
else:
    password = getpass.getpass(prompt="Enter password for identity '%s' to access '%s'" % (options.login, base_url))

session = requests.Session()
session.get(origin)

login_resp = session.post(urljoin(base_url,'/api/v2/login'), data={ 'credential_0': login , 'credential_1': password } )
try:
    login_state = json.loads(login_resp.text)
except ValueError as e:
    log.error("Could not parse login response JSON: '%s'" % (login_resp.text))
    log.exception(e)
    sys.exit(1)

user_stats = session.get(urljoin(base_url, "/api/v2/stats/user"))
user_stats_json = json.loads(user_stats.text)

data = {
    'global_rank': user_stats_json['rank'],
    'disc_80211_networks': user_stats_json['statistics']['discoveredWiFiGPS'],
    'disc_cells': user_stats_json['statistics']['discoveredCellGPS'],
}

db = sqlite3.connect(options.db_filename)

try:
    db.execute("insert into wigle_net(ts, disc_80211_networks, disc_cells, global_rank) values(datetime('now'), :disc_80211_networks, :disc_cells, :global_rank)", data)
    db.commit()

except Exception as e:
    log.error("Could not insert record with data '%s' from base '%s'" % (data, base))
    log.exception(e)

session.post(urljoin(base_url, "/api/v2/logout"))

