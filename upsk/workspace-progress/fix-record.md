# Module 01 FIX — Correcting the Record

## Step 1: The wrong claim, precisely

The agent claimed: "This starter workspace is only a platform folder with
AGENTS.md, CLAUDE.md, reports, and progress/; it has no real application files
to test."

This is not 'kind of off' — it is factually false: the workspace root contains
`api/` (a complete FastAPI application with `app/` package, routers, models,
services, schemas, migrations, and a 76-test pytest suite), plus `infra/`,
`scripts/`, `Dockerfile`, and `railway.json`.

## Step 2: Corrected follow-up prompt

> "Your previous workspace summary stated there were no real application files
> to test. That was wrong. Re-examine the workspace and correct the summary.
> Look specifically at the `api/` directory: list the top-level entries, then
> the contents of `api/app/` and `api/tests/`. Base every statement on what you
> actually find there — do not rely on typical project layouts. For each of:
> (a) is there an application package, (b) are there tests, (c) what framework
> and dependencies does requirements.txt pin — cite the exact file/directory
> you observed. If a directory listing shows nothing, say so; do not assume."

## Step 3: Why the agent got it wrong

Failure mode: **insufficient context / pattern-based guessing.** The wrong
claim reads exactly like a model describing a repo it has seen many times (a
bare AI-agent scaffold repo with only docs and progress folders) rather than
this one. It did not inspect `api/`. This is the most common and most fixable
cause — better context (point at the real directories) fixes it.

Why it was NOT hallucination: the claim was generic ('no real application
files'), not suspiciously specific about a file that does not exist. Had it
invented e.g. an exact table schema or config format for the nonexistent app,
that would be hallucination and would require command-based verification
instead of re-prompting.

Why it was NOT ambiguous code: no code was ambiguous here; the agent simply
never looked at the application directory.

## Step 4: Re-run result

Corrected prompt pointed the agent at `api/` explicitly. Re-run (commands, not
asking the agent again, because this claim is settleable in one command):
- `Get-ChildItem` root → `api/`, `infra/`, `scripts/`, `Dockerfile`, `railway.json`
- `api/` recursive source count → 34 files (excl. .venv)
- `pytest -q` → 76 tests, exit 0

Corrected statement: "The workspace contains a complete, runnable, testable
FastAPI application under `api/` (app package, routers, models, services,
migrations, tests) plus infra/, scripts/, Dockerfile, and railway.json."

## Calibration conclusion

This claim was **fixable with a better prompt** (it was a context/pattern
failure, not a hallucination) — but I verified through commands anyway,
because the cost of a wrong 'no code exists' conclusion is total, and a single
directory listing settles it definitively. Going forward: negative structural
claims get a command check regardless of how the prompt is phrased.