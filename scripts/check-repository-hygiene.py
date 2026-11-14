"""Reject accidentally tracked local data and operational reports."""
import pathlib
import subprocess
paths = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
bad = []
for name in filter(None, paths):
    p = pathlib.PurePosixPath(name)
    private = p.suffix in {".sqlite", ".sqlite3", ".pyc", ".pem"} or "__pycache__" in p.parts
    private |= p.name.startswith(".env") and p.name != ".env.example"
    private |= name.startswith("cs396project1/media/")
    private |= p.match("*OWNERSHIP*AUDIT*.md") or p.match("*auth-repair*.md") or p.match("*infrastructure-audit*.md")
    if private:
        bad.append(name)
if bad:
    raise SystemExit("Private artifacts must not be tracked: " + ", ".join(bad))
print("Repository hygiene passed")
