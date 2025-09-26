#!/bin/bash

export LANGSMITH_PROJECT=daodejing

# Default values
CONCURRENCY=40
NUM_TRIALS=1
END_INDEX=40
EXPERIMENT_ID=""
MODEL="gpt-4o"

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --concurrency)
            CONCURRENCY="$2"
            shift; shift
            ;;
        --num-trials)
            NUM_TRIALS="$2"
            shift; shift
            ;;
        --end-index)
            END_INDEX="$2"
            shift; shift
            ;;
        --experiment-id)
            EXPERIMENT_ID="$2"
            shift; shift
            ;;
        --model)
            MODEL="$2"
            shift; shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# If EXPERIMENT_ID is set, prepend --existing
EXPERIMENT_ID_ARG=""
if [[ -n "$EXPERIMENT_ID" ]]; then
    EXPERIMENT_ID_ARG="--existing $EXPERIMENT_ID"
fi

echo "Running experiments with concurrency $CONCURRENCY, num_trials $NUM_TRIALS, end_index $END_INDEX, experiment_id $EXPERIMENT_ID"

# Start langgraph server
# echo "Starting langgraph server..."
# N_JOBS_PER_WORKER=40 uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --no-browser > /dev/null 2>&1 & echo $! > .langgraph.pid
# echo "Waiting for server to start..."
# sleep 2
echo "Running experiments..."

# Function to cleanup server on exit
# cleanup() {
#     echo "Cleaning up server..."
#     kill $(cat .langgraph.pid) && rm .langgraph.pid
#     exit $1
# }

# Setup trap to ensure cleanup on script interruption
trap "cleanup 1" INT TERM

# Flat agent experiments:
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "single" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 0 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "single" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 1 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "single" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 2 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "single" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 4 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "single" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 6 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "single" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 8 --num-trials $NUM_TRIALS


# Supervisor. Need at least one distractor for it to actually be interesting

# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor-forwarding-and-invisihandoffs" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 1 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor-forwarding-and-invisihandoffs" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 2 --num-trials $NUM_TRIALS
uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor-forwarding-and-invisihandoffs" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 4 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor-forwarding-and-invisihandoffs" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 6 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor-forwarding-and-invisihandoffs" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 8 --num-trials $NUM_TRIALS

# Noisy: supervisor (keep all handoffs in context; no forward message tools)
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 1 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 2 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 4 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 6 --num-trials $NUM_TRIALS

# # Supervisor ablations
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor-invisihandoffs" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 8 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor-forwarding" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 8 --num-trials $NUM_TRIALS 
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor-forwarding-and-invisihandoffs-transfer-prefix" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 8 --num-trials $NUM_TRIALS 
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 8 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "supervisor-transfer-prefix" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 8 --num-trials $NUM_TRIALS


# Swarm tree. Swarm but the sub-agents aren't directly aware of each other. Or supervisor but where it actually transfers


# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "tree" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 1 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "tree" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 2 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "tree" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 4 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "tree" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 6 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "tree" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 8 --num-trials $NUM_TRIALS

# Swarm

# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "swarm" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 1 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "swarm" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 2 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "swarm" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 4 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "swarm" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 6 --num-trials $NUM_TRIALS
# uv run --with-editable . python mabench/run.py --model "$MODEL" --user-model "gpt-4o" --agent-strategy "swarm" --env "combined" --end-index $END_INDEX --max-concurrency $CONCURRENCY --n-distractors 8 --num-trials $NUM_TRIALS

find ./results -name "*.json" -exec stat -f "%m %N" {} + | sort -nr | cut -d' ' -f2- | while read file; do echo -n "$file: "; jq 'reduce .[] as $item ({"sum":0,"count":0}; .sum += $item.reward | .count += 1) | .sum / .count' "$file"; done

# Cleanup server
# cleanup 0
