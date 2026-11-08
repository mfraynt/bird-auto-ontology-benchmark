#!/usr/bin/env bash
# Build the ontology and run both arms on all 500 BIRD Mini-Dev questions.
# Run from the root of an NVIDIA/auto-ontology-eval checkout whose .env follows
# config/env.example, with the services in scripts/start_services.md running.
set -euo pipefail

mkdir -p runs/full_haiku

# 1. Ingest + semantic compile (~8 min, ~$1 on Haiku 5.5).
#    Reset the Postgres catalog first (see start_services.md).
caffeinate -i uv run python main.py --database-name bird --skip-eval 2>&1 | tee runs/build_haiku.log

# 2. Smoke test: 3 questions, both arms.
uv run python main.py --database-name bird --skip-ingest --skip-semantic \
  --limit 3 --run-dir runs/smoke_haiku 2>&1 | tee runs/smoke_haiku.log

# 3. Full run in 5 chunks of 100 (~45 min each with 3 workers).
#    Questions are grouped by database, so chunks are not stratified samples.
for s in 0 100 200 300 400; do
  caffeinate -i uv run python main.py --database-name bird --skip-ingest --skip-semantic \
    --start-index "$s" --end-index $((s + 100)) --eval-workers 3 \
    --run-dir "runs/full_haiku/chunk_$s" 2>&1 | tee "runs/full_haiku/chunk_$s.log"
done
