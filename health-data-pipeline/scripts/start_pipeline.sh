#!/bin/bash
# Starts Docker Desktop, waits for it to be ready, starts Astro, triggers the DAG.
# Called by launchd at the scheduled wake time.

# launchd gives a minimal PATH — add the dirs where docker/astro/homebrew live.
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

LOG="/Users/pedro/Coding Projects/health-data-pipeline/logs/pipeline.log"
PROJECT="/Users/pedro/Coding Projects/health-data-pipeline"
DAG_ID="oura_pipeline"

mkdir -p "$(dirname "$LOG")"
exec >> "$LOG" 2>&1

echo ""
echo "===== $(date '+%Y-%m-%d %H:%M:%S') START ====="

# Hold the machine awake for ~22 min so it doesn't re-sleep mid-run
# (covers extraction + dbt build + the 6:20 stop job). Backgrounded so it
# doesn't block; it exits on its own after the timeout.
caffeinate -i -t 1320 &
echo "caffeinate holding system awake (pid $!)"

# Start Docker Desktop if not running
if ! docker info > /dev/null 2>&1; then
    echo "Starting Docker Desktop..."
    open -a Docker
    # Wait up to 90s for Docker to be ready
    for i in $(seq 1 90); do
        sleep 1
        if docker info > /dev/null 2>&1; then
            echo "Docker ready after ${i}s"
            break
        fi
        if [ "$i" -eq 90 ]; then
            echo "ERROR: Docker did not start within 90s. Aborting."
            exit 1
        fi
    done
else
    echo "Docker already running"
fi

# Start Astro (idempotent — safe to call if already running)
echo "Starting Astro..."
cd "$PROJECT"
astro dev start 2>&1

# Wait for webserver to be healthy
echo "Waiting for Airflow webserver..."
for i in $(seq 1 60); do
    sleep 2
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:6563/health 2>/dev/null | grep -q "200"; then
        echo "Airflow ready after $((i*2))s"
        break
    fi
    if [ "$i" -eq 60 ]; then
        echo "WARNING: Airflow did not become healthy — triggering anyway"
    fi
done

# Trigger the DAG
echo "Triggering DAG: $DAG_ID"
astro dev run dags trigger "$DAG_ID" 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S') START DONE ====="
