import sqlite3

conn = sqlite3.connect('digital_twin_production.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=== DATABASE: digital_twin_production.db ===")
print(f"Tables found: {len(tables)}\n")

for t in tables:
    name = t[0]
    cursor.execute(f"SELECT COUNT(*) FROM [{name}]")
    count = cursor.fetchone()[0]
    print(f"  Table: {name} — {count} rows")
    
    # Show last 3 rows
    cursor.execute(f"SELECT * FROM [{name}] ORDER BY id DESC LIMIT 3")
    rows = cursor.fetchall()
    cols = [desc[0] for desc in cursor.description]
    print(f"  Columns: {cols}")
    for r in rows:
        print(f"    {r}")
    print()

conn.close()
