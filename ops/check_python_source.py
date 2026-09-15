"""Dependency-free source audit in the matching Debian development stage."""
import ast
import json
import sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
files = sorted(list((root / 'apps').rglob('*.py')) + list((root / 'config').rglob('*.py')))
for path in files:
    ast.parse(path.read_text(), filename=str(path))
(root / 'source-check.json').write_text(json.dumps({'python_sources_parsed': len(files), 'native_artifacts_copied': False}) + '\n')
