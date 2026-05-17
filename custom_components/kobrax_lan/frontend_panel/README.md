# Kobrax LAN Frontend Panel Source

This folder is the source-of-truth for the Kobrax LAN Lovelace card build.

## Build Card

From this folder:

```bash
npm ci
npm run build_card:quick
```

Build output:

- dist/kobrax-lan-card.js

## Export To Card Repo

After building, copy the artifact to the HACS card distribution repo:

- Windows PowerShell:

```powershell
./scripts/export-card-to-repo.ps1
```

- Linux/macOS:

```bash
./scripts/export-card-to-repo.sh
```

Default export target:

- ../../../../kobrax-lan-hass-card/kobrax-lan-card.js

Override export target by setting CARD_REPO_PATH.
