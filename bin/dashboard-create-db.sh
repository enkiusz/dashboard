#!/bin/sh

readonly INSERT_TEST_DATA=1

while [ "$1" ]; do
    dbfile="$1"; shift
    echo "Creating new database in file '$dbfile'"
    sqlite3 "$dbfile" <<EOF
create table if not exists wigle_net (ts TEXT, disc_80211_networks INT, disc_cells INT, global_rank INT);
create table if not exists aero2_data (ts TEXT, imsi TEXT, expiration_ts TEXT, data_used INT, data_available INT);
EOF

    if [ -n "$INSERT_TEST_DATA" ]; then
        sqlite3 "$dbfile" <<EOF
insert into wigle_net (ts, disc_80211_networks, disc_cells, global_rank) values(datetime('now', '-2 day'), 10, 5, 1300);
insert into wigle_net (ts, disc_80211_networks, disc_cells, global_rank) values(datetime('now', '-1 day'), 15+abs(random() % 100), 8+abs(random() % 10), 1100 - abs(random() % 50) );
insert into wigle_net (ts, disc_80211_networks, disc_cells, global_rank) values(datetime('now'), 200+abs(random() % 500), 30+abs(random() % 10), 1000 - abs(random() % 50) );
EOF

        #TODO: Add test data for aero2 data
    fi
    done
