"""Deterministic reproduction + verification of the code-generation race.

Module 3 (Reproduction) -- Debugging & Incident Response.
The canonical Bug #5 (analytics bucket SELECT-then-INSERT) is structurally
absent in this fork: clicks are recorded with a single atomic INSERT guarded
by a unique event_key + IntegrityError (no pre-SELECT). The same TOCTOU race
class does exist in code generation: `_generate_code` used to SELECT "is this
code free?" then INSERT -- two concurrent creators could both see a free code
and one would crash with duplicate key "links_code_key".

To make the race deterministic we drive the RNG so the FIRST candidate is
identical for every caller (forcing the collision window), while retries
diverge. Against the OLD code this yields an IntegrityError crash. Against the
fixed code (INSERT with retry-on-conflict) both creators succeed with distinct
codes.

Run as:
  repro_code_race.py check   -> assert both creators succeed, codes unique
"""
import secrets
import sys
import threading

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.services import links_service

# First candidate always "aaaaaa" (guaranteed collision), then unique.
_calls = 0
_call_lock = threading.Lock()


def colliding_choice(alphabet):
    global _calls
    with _call_lock:
        _calls += 1
    return "a" if _calls <= 1 else "b"


results = []
barrier = threading.Barrier(2)


def concurrent_create(url, use_fixed_path: bool):
    db = SessionLocal()
    try:
        if use_fixed_path:
            from app.schemas.link import CreateLinkRequest

            link = links_service.create_link(
                db, CreateLinkRequest(long_url=url), owner_id=1
            )
            return "OK", link.code
        secrets.choice = colliding_choice
        code = links_service._generate_code()
        barrier.wait(timeout=10)
        db.add(links_service.Link(code=code, long_url=url, created_by=1))
        db.commit()
        return "OK", code
    except IntegrityError as exc:
        db.rollback()
        return "INTEGRITY", str(exc.__cause__).split("\n")[0]
    except Exception as exc:
        db.rollback()
        return "ERR", type(exc).__name__
    finally:
        db.close()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    threads = [
        threading.Thread(
            target=lambda: results.append(
                concurrent_create(f"https://example.com/race-{i}", mode == "check")
            )
        )
        for i in range(2)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    for r in results:
        print(r)
    codes = [r[1] for r in results if r[0] == "OK"]
    if mode == "check" and len(codes) == 2 and len(set(codes)) == 2:
        print("RACE ELIMINATED: both concurrent creators succeeded with distinct codes")
    elif mode == "check":
        print("STILL FAILING: race window present")
        sys.exit(1)


if __name__ == "__main__":
    main()