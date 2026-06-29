#!/bin/bash
# Stops the Astro stack. Called by launchd after the pipeline has had time to finish.

# launchd gives a minimal PATH — add the dirs where docker/astro/homebrew live.
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

LOG="/Users/pedro/Coding Projects/health-data-pipeline/logs/pipeline.log"
PROJECT="/Users/pedro/Coding Projects/health-data-pipeline"

mkdir -p "$(dirname "$LOG")"
exec >> "$LOG" 2>&1

echo ""
echo "===== $(date '+%Y-%m-%d %H:%M:%S') STOP ====="

cd "$PROJECT"
astro dev stop 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S') STOP DONE ====="
