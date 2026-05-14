# Backup And Recovery

This repository now includes a repo-owned helper at `deployment/backup_restore.py` for backing up and restoring the two data stores that matter for this checkout:

- PostgreSQL data in the `srp-ats-db` container
- Uploaded resume files in the `srp_ats_uploads` Docker volume

## What To Back Up

Minimum trusted backup set:

1. Database dump (`database.sql`)
2. Uploads archive (`uploads.tar.gz`)
3. Backup manifest (`manifest.json`)

These are created together so the database and uploaded files stay in sync.

## Create A Backup

Run this on the deployment host from the repository root:

```bash
python deployment/backup_restore.py backup --output-dir backups
```

That creates a timestamped directory under `backups/`, for example:

```text
backups/20260513T010203Z/
  database.sql
  uploads.tar.gz
  manifest.json
```

## Verify A Backup Target

Before and after backup windows, verify the live data stores are reachable:

```bash
python deployment/backup_restore.py verify
```

This checks PostgreSQL readiness and lists a sample of files from the uploads volume.

## Restore Procedure

Restores are destructive. Only restore into the intended environment, and confirm you are targeting the correct containers/volumes first.

```bash
python deployment/backup_restore.py restore backups/<timestamp> --force
```

## Recommended Recovery Runbook

1. Stop or isolate write traffic to the app.
2. Capture a fresh emergency backup before restoring anything.
3. Restore the selected backup using `deployment/backup_restore.py`.
4. Run `python deployment/backup_restore.py verify`.
5. Check app health:
   - `curl http://127.0.0.1:8009/health`
   - confirm expected resume files exist
   - confirm authenticated ATS flows still work
6. Re-enable traffic only after verification passes.

## Operational Recommendations

- Keep backups outside the Docker host as well; local-only backups are not enough for disaster recovery.
- Protect backup directories with OS permissions because they contain candidate data.
- Test one restore regularly. A backup that has never been restored is not yet trusted.
- Keep `DB_AUTO_INIT=false` in production so schema creation does not mask migration or restore mistakes.
