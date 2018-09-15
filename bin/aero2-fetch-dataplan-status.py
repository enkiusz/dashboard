#!/usr/bin/env python3

# aero2 - fetch the dataplan status
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

import requests, sys, json, logging, datetime, pytz
import sqlite3

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
    print('A aero2 login is required')
    sys.exit(1)

if options.password_file is not None:
    password = open(options.password_file, "rb").read().strip()

db = sqlite3.connect(options.db_filename)

session = requests.Session()
login_resp = session.post(urljoin(base_url,'/api/v2/login'), data={ 'credential_0': login , 'credential_1': password} )
login_state = json.loads(login_resp.text)

class Aero2Session():
    def __init__(self):
        self._s = requests.session()
        self.base_url = 'https://moje.aero2.pl/ProstyPrepaid/'

    def get(self, url, **kwargs):
        return self._s.get(urljoin(self.base_url, url), **kwargs)

    def post(self, url, **kwargs):
        return self._s.post(urljoin(self.base_url, url), **kwargs)

s = Aero2Session()

log.debug("Using identity '%s'" % (login))

r = s.get('selfcare/isLogin')
log.debug(r.text)

r = s.get('selfcare/getICCID')
log.debug(r.text)

r = s.post('selfcare/login', json={"login": login, "password": password})
log.debug(r.text)

r = s.get("shop/getAllOffers")

# Update available dataplans
for dataplan in r.json()['data']:
    log.debug(dataplan)

    try:

        data = {
            'id': dataplan['typeId'],
            'name': dataplan['name'],
            'days_valid': dataplan['period'],
            'price': dataplan['price'],
            'volume': dataplan['size']
        }

        data['speed'] = dataplan['speed']
        if data['speed'] == 'bez limitu':
            data['speed'] = None

        db.execute("insert or ignore into aero2_dataplans(id, name, days_valid, speed, price, volume) values(:id, :name, :days_valid, :speed, :price, :volume)", data)
        db.commit()

    except Exception as e:
        log.fatal("Could not insert dataplan offer record with data '%s'" % (data))
        log.exception(e)

r = s.get("shop/getClientType/%s" % (login))
log.debug(r.text)

r = s.get("selfcare/getClientInfo")
log.debug(r.text)

exp_ts = None
data_used = None
data_total = None
dataplan_id = 0 # This is the default free plan (aka. BDI)

client_info = json.loads(r.text)
imsi = client_info["data"]["loginData"]["cardNumber"]

current_dataplan = client_info["data"]["currentPackage"]

if current_dataplan is not None:
    log.debug("pkg: %s" % (current_pkg))

    exp_ts = pytz.timezone("Europe/Warsaw").localize( datetime.datetime.strptime(current_pkg['expirationDate'], '%d.%m.%Y godzina %H:%M') ).isoformat()
    data_used = current_pkg['totalLimitsUsed']
    data_total = current_pkg['totalLimit']

log.info("IMSI %s expires @%s (used %s of total %s MB)" % (imsi, exp_ts, data_used, data_total))

try:
    data = {
        "imsi": imsi,
        "dataplan_id": dataplan_id,
        "expiration_ts": exp_ts,
        "data_used": data_used,
        "data_available": data_total,
    }

    db.execute("insert into aero2_data(ts, imsi, dataplan_id, expiration_ts, data_used, data_available) values(datetime('now'), :imsi, :dataplan_id, datetime(:expiration_ts), :data_used, :data_available)", data)
    db.commit()

except Exception as e:
    log.error("Could not insert record with data '%s' from base '%s'" % (data, base))
    log.exception(e)

# We don't want to buy a package yet
#r = s.post("shop/checkCanBuy", json={"cardNumber":login, "offerIds":[1045]})
#print(r.text)

#r = s.post("selfcare/reserveOffer", json={"offerIds":[1045],"cardNumber":"8948171200000636044"})
#print(r.text)

