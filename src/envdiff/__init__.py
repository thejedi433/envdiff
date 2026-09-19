#!/usr/bin/env python3
"""Compare .env files across environments and find missing or mismatched keys."""

import argparse
import sys
from pathlib import Path
from typing import Dict, Tuple


def parse_env_file(path: Path) -> Dict[str, str]:
    """Parse a .env file and return key-value pairs."""
    env_vars = {}
    if not path.exists():
        return env_vars
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            # Handle KEY=VALUE format
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                # Remove surrounding quotes if present
                if len(value) >= 2:
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                if key:
                    env_vars[key] = value
    
    return env_vars


def compare_envs(file1: Path, file2: Path) -> Tuple[Dict[str, Tuple[str, str]], Dict[str, str], Dict[str, str]]:
    """
    Compare two .env files.
    
    Returns:
        - diff: keys with different values {key: (val1, val2)}
        - only_in_1: keys only in file1
        - only_in_2: keys only in file2
    """
    env1 = parse_env_file(file1)
    env2 = parse_env_file(file2)
    
    keys1 = set(env1.keys())
    keys2 = set(env2.keys())
    
    only_in_1 = {k: env1[k] for k in keys1 - keys2}
    only_in_2 = {k: env2[k] for k in keys2 - keys1}
    
    common_keys = keys1 & keys2
    diff = {}
    for key in common_keys:
        if env1[key] != env2[key]:
            diff[key] = (env1[key], env2[key])
    
    return diff, only_in_1, only_in_2


def format_output(diff: Dict[str, Tuple[str, str]], only_in_1: Dict[str, str], 
                  only_in_2: Dict[str, str], label1: str, label2: str) -> str:
    """Format comparison results for display."""
    lines = []
    
    if not diff and not only_in_1 and not only_in_2:
        return f"✓ Files are identical: {label1} and {label2}"
    
    if diff:
        lines.append(f"\n⚠ Different values ({len(diff)}):")
        for key, (val1, val2) in sorted(diff.items()):
            lines.append(f"  {key}:")
            lines.append(f"    {label1}: {val1 or '(empty)'}")
            lines.append(f"    {label2}: {val2 or '(empty)'}")
    
    if only_in_1:
        lines.append(f"\n✗ Only in {label1} ({len(only_in_1)}):")
        for key in sorted(only_in_1.keys()):
            lines.append(f"  {key} = {only_in_1[key] or '(empty)'}")
    
    if only_in_2:
        lines.append(f"\n✗ Only in {label2} ({len(only_in_2)}):")
        for key in sorted(only_in_2.keys()):
            lines.append(f"  {key} = {only_in_2[key] or '(empty)'}")
    
    return '\n'.join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Compare .env files across environments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  envdiff .env .env.local
  envdiff .env.development .env.production
  envdiff ../project1/.env ../project2/.env
        '''
    )
    parser.add_argument('file1', type=Path, help='First .env file')
    parser.add_argument('file2', type=Path, help='Second .env file')
    
    args = parser.parse_args()
    
    if not args.file1.exists():
        print(f"Error: {args.file1} not found", file=sys.stderr)
        sys.exit(1)
    
    if not args.file2.exists():
        print(f"Error: {args.file2} not found", file=sys.stderr)
        sys.exit(1)
    
    diff, only_in_1, only_in_2 = compare_envs(args.file1, args.file2)
    output = format_output(diff, only_in_1, only_in_2, str(args.file1), str(args.file2))
    print(output)
    
    # Exit with error code if differences found (useful for CI)
    if diff or only_in_1 or only_in_2:
        sys.exit(1)


if __name__ == '__main__':
    main()
