import sqlite3

conn = sqlite3.connect('profileiq_v2.db')
cur = conn.cursor()
cur.execute('PRAGMA table_info(module_scores)')
existing = {r[1] for r in cur.fetchall()}

new_cols = [
    ('behavior_anomaly_score',  'REAL DEFAULT 0.0'),
    ('behavior_flags',          'TEXT DEFAULT ""'),
    ('behavior_source',         'TEXT DEFAULT "mock"'),
    ('profile_type',            'TEXT DEFAULT "unknown"'),
    ('profile_entities',        'TEXT DEFAULT ""'),
    ('profile_summary',         'TEXT DEFAULT ""'),
    ('profile_type_confidence', 'REAL DEFAULT 0.0'),
]

added = []
for col, typedef in new_cols:
    if col not in existing:
        cur.execute(f'ALTER TABLE module_scores ADD COLUMN {col} {typedef}')
        added.append(col)

conn.commit()
cur.execute('PRAGMA table_info(module_scores)')
final = [r[1] for r in cur.fetchall()]
conn.close()

with open('migrate_behavior_result.txt', 'w') as f:
    f.write(f"Added: {added}\nFinal: {final}\nOK\n")
