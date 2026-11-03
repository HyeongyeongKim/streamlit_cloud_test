"""Preserve the locally edited, separately versioned Sites backend in this repo."""
from pathlib import Path
import difflib
import subprocess

root = Path(__file__).resolve().parents[1]
backend = root / 'sites' / 'oneul-garden'
tracked = ['app/api/data/route.ts', 'db/schema.ts', 'drizzle/meta/_journal.json']
created = ['app/schedule-rules.ts', 'drizzle/0002_common_omega_red.sql', 'drizzle/meta/0002_snapshot.json']
patch = subprocess.check_output(['git', 'diff', '--no-ext-diff', '--', *tracked], cwd=backend).decode('utf-8')
for name in created:
    content = (backend/name).read_text(encoding='utf-8').splitlines(keepends=True)
    patch += f'diff --git a/{name} b/{name}\nnew file mode 100644\n'
    for line in difflib.unified_diff([], content, fromfile='/dev/null', tofile='b/'+name):
        patch += line if line.endswith('\n') else line + '\n\\ No newline at end of file\n'
destination = root / 'backend_changes' / 'schedule-v1.patch'
destination.parent.mkdir(exist_ok=True)
destination.write_text(patch, encoding='utf-8', newline='\n')
print(destination.relative_to(root))
