#!/usr/bin/env python3

# wiglestats - User stats render
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

import asciitable, sqlite3, datetime

#
# Parse command line options
#
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-d', '--db', dest='db_filename', help='Use DB as the source sqlite database', metavar='DB')

(options, args) = parser.parse_args()

db = sqlite3.connect(options.db_filename)

cur = db.cursor()
cur.execute("select strftime('%s', 'now') - strftime('%s', ts) as delta,imsi,aero2_dataplans.name,expiration_ts,data_used,data_available from aero2_data join aero2_dataplans where aero2_dataplans.id = aero2_data.dataplan_id order by ts desc limit 1")
delta, imsi, dataplan_name, expiration_ts, data_used, data_available = cur.fetchone()

delta = datetime.timedelta(seconds=delta)

asciitable.write({
    'UPD': [ str(delta) ],
    'IMSI': [ imsi ],
    'Dataplan': [ dataplan_name ],
    'Expiration date': [ str(expiration_ts) ],
    'Data usage': [ "%s of %s MB" % (data_used, data_available) ],
}, names = ['UPD', 'IMSI', 'Dataplan', 'Expiration date', 'Data usage'], Writer=asciitable.FixedWidth)


