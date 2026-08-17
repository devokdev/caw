import json, sys
sys.path.insert(0, r"C:\Users\karta\Desktop\New folder\upsk-system-design-workspace\api")

from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()
results = {}

cols = db.execute(text("""
  SELECT column_name FROM information_schema.columns
  WHERE table_name = 'teams' ORDER BY column_name
""")).fetchall()
results["teams_columns"] = [c[0] for c in cols]

roles = db.execute(text("""
  SELECT DISTINCT role FROM team_members ORDER BY role
""")).fetchall()
results["distinct_roles"] = [r[0] for r in roles]

owner_check = db.execute(text("""
  SELECT t.id, t.created_by,
    EXISTS(SELECT 1 FROM team_members m
           WHERE m.team_id = t.id AND m.user_id = t.created_by) AS owner_in_members
  FROM teams t LIMIT 3
""")).fetchall()
results["owner_not_in_members"] = [{"id": r[0], "created_by": r[1], "owner_in_members": r[2]} for r in owner_check]

constraints = db.execute(text("""
  SELECT conname FROM pg_constraint
  WHERE conrelid IN (SELECT oid FROM pg_class
                     WHERE relname IN ('teams','team_members','invitations'))
  ORDER BY conname
""")).fetchall()
results["constraints"] = [c[0] for c in constraints]

invite_meta = db.execute(text("""
  SELECT column_name FROM information_schema.columns
  WHERE table_name = 'invitations' ORDER BY column_name
""")).fetchall()
results["invitations_columns"] = [c[0] for c in invite_meta]

db.close()
print(json.dumps(results, indent=2))