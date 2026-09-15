#!/usr/bin/env python3
"""Deterministic repository whitespace gate; --fix normalizes LF and trims trailing spaces."""
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--fix',action='store_true');args=parser.parse_args()
ignored={'node_modules','.venv','.git','secrets','runtime','backups','staticfiles','__pycache__','.pytest_cache','.ruff_cache','test-results','playwright-report'}
issues=[]
for path in sorted(ROOT.rglob('*')):
    if not path.is_file() or any(part in ignored for part in path.relative_to(ROOT).parts): continue
    if path.suffix not in {'.py','.ts','.tsx','.js','.mjs','.json','.yaml','.yml','.toml','.md','.css','.html','.sh','.in','.env','.example'} and path.name not in {'Dockerfile','Makefile','dc'}: continue
    text=path.read_text()
    normalized='\n'.join(line.rstrip() for line in text.splitlines())+('\n' if text else '')
    if text!=normalized:
        issues.append(str(path.relative_to(ROOT)))
        if args.fix:path.write_text(normalized)
if issues and not args.fix: raise SystemExit('Whitespace differences: '+', '.join(issues))
print('Whitespace gate passed.' if not args.fix else f'Normalized {len(issues)} files.')
