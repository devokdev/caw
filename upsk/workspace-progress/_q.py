import sqlalchemy as sa

e = sa.create_engine("postgresql://postgres:postgres@localhost:5432/upsk_sdf")
with e.begin() as c:
    n = c.execute(sa.text("SELECT count(*) FROM links")).scalar()
    print("links rows:", n)
    ids = [r[0] for r in c.execute(sa.text("SELECT id FROM links ORDER BY id LIMIT 5"))]
    print("first ids:", ids)