import sqlalchemy as sa

e = sa.create_engine("postgresql://postgres:postgres@localhost:5432/upsk_sdf")
with e.begin() as c:
    rows = c.execute(sa.text(
        "SELECT link_id, event_key, clicked_at FROM click_events "
        "WHERE link_id IN (6116, 6117) ORDER BY clicked_at"
    )).all()
    print(f"click_events rows for link 6116/6117: {len(rows)}")
    for r in rows:
        print(f"  link_id={r[0]} event_key={r[1][:12]} clicked_at={r[2]}")
    for lid in (6116, 6117):
        n = c.execute(sa.text("SELECT count(*) FROM click_events WHERE link_id=:l"), {"l": lid}).scalar()
        print(f"link {lid}: {n} click events")