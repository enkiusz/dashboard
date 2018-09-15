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

import asciitable
import sqlite3
import datetime
from optparse import OptionParser

#
# Parse command line options
#

parser = OptionParser()
parser.add_option('-d', '--db', dest='db_filename', help='Use DB as the source sqlite database', metavar='DB')

(options, args) = parser.parse_args()

db = sqlite3.connect(options.db_filename)

cur = db.cursor()
cur.execute("select strftime('%s', 'now') - strftime('%s', ts) as delta,cud_id,ku_id,balance from innogy_data group by cud_id, ku_id order by delta asc")

deltas = []
cuds = []
kus = []
balances = []
for row in cur.fetchall():
    deltas.append( str(datetime.timedelta(seconds=row[0])) )
    cuds.append(row[1])
    kus.append(row[2])
    balances.append(row[3])

asciitable.write({
    'UPD': deltas,
    'CUD': cuds,
    'KU': kus,
    'Balance (PLN)': balances,
}, names = ['UPD', 'CUD', 'KU', 'Balance (PLN)' ], Writer=asciitable.FixedWidth)


