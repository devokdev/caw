import psycopg2
c = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/upsk_sdf")
cur = c.cursor()
cur.execute("select table_name from information_schema.tables where table_schema='public' order by table_name")
print("tables:", [r[0] for r in cur.fetchall()])
for t in ("click_events", "analytics", "links", "users"):
    cur.execute("select to_regclass(%s)", (t,))
    if cur.fetchone()[0]:
        cur.execute("select column_name, data_type from information_schema.columns where table_name=%s order by ordinal_position", (t,))
        print(t, ":", cur.fetchall())
cur.execute("select count(*) from click_events")
print("click_events rows:", cur.fetchone()[0])
cur.execute("select count(*) from links")
print("links rows:", cur.fetchone()[0])
c.close()