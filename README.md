# envdiff

Compare `.env` files across environments and find missing or mismatched keys.

## What it does

`envdiff` parses two `.env` files and shows:
- Keys with different values
- Keys only in the first file
- Keys only in the second file

Perfect for:
- Syncing dev/staging/prod environment configs
- CI checks ensuring environments stay in sync
- Finding missing keys when deploying to new environments

## Install

```bash
pip install envdiff
```

## Usage

```bash
# Compare dev and production
envdiff .env.development .env.production

# Compare two projects
envdiff ../project1/.env ../project2/.env
```

### Example output

```
⚠ Different values (2):
  DB_HOST:
    .env.dev: localhost
    .env.prod: prod-db.example.com
  DEBUG:
    .env.dev: true
    .env.prod: false

✗ Only in .env.dev (1):
  DEV_ONLY_KEY = some_value

✗ Only in .env.prod (1):
  NEW_RELIC_KEY = newrelic-123
```

### Exit codes

- `0` — files are identical
- `1` — differences found (useful for CI)

## CI usage

```yaml
- name: Check env files in sync
  run: envdiff .env.example .env.production
```

## License

MIT
