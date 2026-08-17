"""Module 5 FIX: demonstrate data-loss recovery mechanics on a throwaway
staging table (mirrors `links`) so no production data is touched.

Emulates the incident's PITR scenario: snapshot a copy of links (the
'backup'), simulate attacker deletion of rows, then restore the deleted rows
from the snapshot and verify they resolve again. Concrete mechanics behind
the recovery plan (query backup -> extract -> re-insert -> verify -> notify).
"""
import sqlalchemy as sa

ENGINE = "postgresql://postgres:postgres@localhost:5432/upsk_sdf"


def main():
    e = sa.create_engine(ENGINE)
    with e.begin() as c:
        c.execute(sa.text("DROP TABLE IF EXISTS recovery_staging"))
        c.execute(sa.text("CREATE TABLE recovery_staging (LIKE links INCLUDING ALL)"))
        c.execute(sa.text("INSERT INTO recovery_staging SELECT * FROM links WHERE id IN "
                          "(SELECT id FROM links ORDER BY id LIMIT 5)"))
        rows = [dict(r._mapping) for r in c.execute(sa.text("SELECT * FROM recovery_staging ORDER BY id"))]
        print(f"1. backup snapshot (staging): {len(rows)} rows copied from links")

    victims = rows[:3]
    victim_ids = [v["id"] for v in victims]
    with e.begin() as c:
        for v in victims:
            c.execute(sa.text("DELETE FROM recovery_staging WHERE id = :id"), {"id": v["id"]})
        remaining = [r[0] for r in c.execute(sa.text("SELECT id FROM recovery_staging ORDER BY id"))]
        print(f"2. attacker deletes links {victim_ids}; remaining={remaining}")

    with e.begin() as c:
        restored = 0
        for v in victims:
            keys = [k for k in v.keys() if v[k] is not None]
            cols = ", ".join(keys)
            binds = ", ".join(f":{k}" for k in keys)
            c.execute(sa.text(f"INSERT INTO recovery_staging ({cols}) VALUES ({binds}) "
                              f"ON CONFLICT (id) DO NOTHING"), v)
            restored += 1
        print(f"3. PITR restore: re-inserted {restored} rows from backup snapshot")

    with e.begin() as c:
        present = [r[0] for r in c.execute(sa.text("SELECT id FROM recovery_staging ORDER BY id"))]
        recovered = [i for i in victim_ids if i in present]
        print(f"4. verify: {len(present)} rows in staging; deleted IDs present again = {recovered}")
        print("5. notify: affected users told their links were temporarily "
              "unavailable and have been restored")
        c.execute(sa.text("DROP TABLE recovery_staging"))


if __name__ == "__main__":
    main()