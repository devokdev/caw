from app.errors import redact

cases = [
    ("missing bearer token", "missing bearer token"),
    ("invalid or expired token", "invalid or expired token"),
    ("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.abcDEF123_-+", "Authorization: [REDACTED]"),
    ("password=supersecret", "password=[REDACTED]"),
]
ok = True
for src, expected in cases:
    got = redact(src)
    status = "OK " if got == expected else "FAIL"
    if got != expected:
        ok = False
    print(f"{status} in={src!r} -> {got!r} (expected {expected!r})")
print("ALL PASS" if ok else "SOME FAILED")