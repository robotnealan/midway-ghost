@../CLAUDE.md

# robertnealan.com

Personal blog powered by Ghost, hosted on Fly.io.

## Stack

- **CMS**: Ghost 5.87.2 (Alpine Docker image)
- **Theme**: Midway (custom Ghost theme in this repo)
- **Hosting**: Fly.io (`robertnealan-ghost`, SJC region)
- **Database**: SQLite3
- **Storage**: Fly volume (`ghost_data`, 3GB)
- **Domain**: robertnealan.com (Cloudflare Registrar + DNS)
- **Email**: Google Workspace (5 MX records), Mailgun (mg subdomain)

## Fly.io

- **App**: `robertnealan-ghost`
- **Machine**: shared-cpu/1cpu/512MB, auto-stop enabled
- **IPs**: 66.241.125.39 (shared v4), 2a09:8280:1::dc:9174:0 (v6)
- **Volume**: `ghost_data` mounted at `/var/lib/ghost/content`

## Development

Ghost admin: https://robertnealan.com/ghost/

Theme development:
```bash
# Install theme dependencies
npm install

# Deploy theme changes — zip and upload via Ghost admin
zip -r midway.zip assets partials *.hbs package.json
```

## Files

- `fly.toml` — Fly.io deployment config
- `import.py`, `import-direct.py`, `import.sql` — Migration scripts from old Ghost/MySQL
