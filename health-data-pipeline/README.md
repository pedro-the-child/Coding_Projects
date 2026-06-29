# health-data-pipeline

Personal biometric data pipeline: Oura Ring → dlt → BigQuery → dbt → Airflow (Astro CLI).

## Stack

- **Extraction**: dlt with Oura v2 REST API (OAuth2)
- **Storage**: BigQuery (`oura_raw`, `oura_analytics`)
- **Transformation**: dbt (staging → intermediate → marts)
- **Orchestration**: Airflow via Astro CLI (local, scheduled start/stop)

## Setup

1. Copy `.env.example` to `.env` and fill in real values (never commit `.env`)
2. Run OAuth2 flow once via `extraction/oauth_token_store.py` to generate `.tokens.json`
3. Authenticate with GCP: `gcloud auth application-default login`
4. `astro dev start` to launch Airflow locally

## Scheduled runs (macOS launchd)

The pipeline runs daily at 6 AM via launchd, which starts Docker + Astro, triggers
the DAG, then stops the stack (`scripts/start_pipeline.sh`, `scripts/stop_pipeline.sh`).

Setup:

1. Copy the plists from `scripts/launchd/` to `~/Library/LaunchAgents/` and
   `launchctl load` both.
2. Schedule the machine to wake before the run:
   `sudo pmset repeat wakeorpoweron MTWRFSU 05:58:00`
3. **Grant the `astro` binary Full Disk Access** (System Settings → Privacy &
   Security → Full Disk Access → add `/opt/homebrew/Cellar/astro/<version>/bin/astro`).
   This is **required**: the Homebrew `astro` binary is ad-hoc signed, so macOS
   otherwise shows a blocking "astro would like to access data from other apps"
   prompt on every run that cannot be permanently dismissed — it would hang the
   unattended 6 AM run. Re-grant after upgrading astro (the version path changes).

Caveats: the Mac must be **plugged in and not shut down** (asleep is fine — it
wakes itself). Apple Silicon cannot power on from a full shutdown, and launchd
agents require an active login session.

## Security

This repo is public. Credentials are excluded via `.gitignore`. Never commit:
- `.env`
- `.tokens.json`
- Any service account JSON key
