"""Bootstrap: creates the database from schema.sql and imports the 4 seeds by column NAME.
Usage (first run only): cd /workspace/rotina-apps && python3 seed.py rotina.db"""
import csv, os, sqlite3, sys

db = sys.argv[1]
if os.path.exists(db):
    sys.exit('database already exists; seed.py only runs at bootstrap')
con = sqlite3.connect(db)
con.executescript(open('schema.sql', encoding='utf-8').read())
with con:
    for t in ('config', 'benchmarks', 'limiares', 'fontes'):
        with open(f'seed_{t}.csv', encoding='utf-8', newline='') as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            r = {k: (v if v != '' else None) for k, v in r.items()}
            cols = ','.join(r); ph = ','.join('?' * len(r))
            con.execute(f'INSERT INTO {t}({cols}) VALUES({ph})', list(r.values()))
        print(t, len(rows))
print('user_version', con.execute('PRAGMA user_version').fetchone()[0])
print('integrity', con.execute('PRAGMA integrity_check').fetchone()[0])
