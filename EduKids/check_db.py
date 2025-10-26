import sqlite3
import os
# Check parent directory database
db_path = os.path.join('..', 'edukids_db')
print('Checking database at:', db_path)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="django_session";')
tables = cursor.fetchall()
print('django_session table exists:', len(tables) > 0)
if len(tables) > 0:
    try:
        cursor.execute('SELECT COUNT(*) FROM django_session;')
        count = cursor.fetchone()
        print('Rows in django_session:', count[0])
    except Exception as e:
        print('Error querying django_session:', e)
conn.close()