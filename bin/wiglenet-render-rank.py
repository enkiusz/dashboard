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
cur.execute("select strftime('%s', 'now') - strftime('%s', ts) as delta,disc_80211_networks,disc_cells,global_rank from wigle_net order by ts desc limit 1")
delta, disc_80211_networks, disc_cells, global_rank = cur.fetchone()

delta = datetime.timedelta(seconds=delta)

asciitable.write({
    'UPD': [ str(delta) ],
    'Disc. Nets w/ GPS': [ str(disc_80211_networks) ],
    'Disc. cells w/ GPS': [ str(disc_cells) ],
    'Rank': [ str(global_rank) ],
}, names = ['UPD', 'Disc. Nets w/ GPS', 'Disc. cells w/ GPS', 'Rank'], Writer=asciitable.FixedWidth)


