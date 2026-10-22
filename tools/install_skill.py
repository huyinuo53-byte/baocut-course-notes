#!/usr/bin/env python3
"""Copy this Skill only; refuse to overwrite an existing installation."""
import argparse
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', default='~/.agents/skills/baocut-course-notes', help='Full target Skill directory')
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / 'skills/baocut-course-notes'
    raw = Path(args.dest).expanduser()
    if raw.is_symlink() or raw.exists():
        parser.error('Destination exists; choose another --dest. Nothing was overwritten.')
    destination = raw.resolve()
    if destination == source or source in destination.parents:
        parser.error('Destination must be outside the bundled source Skill.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
    print('Installed Skill:', destination)
    print('Restart or refresh your Agent and check that baocut-course-notes is discovered.')
    print('BaoCut, models and other third-party dependencies were not installed.')


if __name__ == '__main__':
    main()
