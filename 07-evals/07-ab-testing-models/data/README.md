# Airline Assistant Data

This directory contains the airline domain tools and datasets used in the A/B Testing tutorials (07a and 07b).

## Contents

### ma-bench/
Multi-Agent Benchmark (MA-Bench) for airline customer service.
- **Source**: Adapted from τ-bench (https://arxiv.org/abs/2406.12045)
- **Contents**: 14 airline domain tools for flight booking, reservations, and customer service
- **Key Files**:
  - `mabench/__init__.py` - Package initialization (required for Python imports)
  - `mabench/environments/airline/tools/` - All 14 airline tools
  - `mabench/environments/airline/data/` - Flight, reservation, and user data

### tau-bench/
τ-bench (Tau Bench) airline environment and test scenarios.
- **Source**: https://arxiv.org/abs/2406.12045
- **Contents**: Airline policy, test scenarios, and evaluation benchmarks
- **Key Files**:
  - `tau_bench/envs/airline/wiki.py` - Airline policy document (WIKI variable)
  - `tau_bench/envs/airline/tasks_singleturn.json` - 50 test scenarios

## Tools Available

The 14 airline tools provide comprehensive customer service capabilities:

**Flight Management:**
- `search_direct_flight` - Find direct flights between cities
- `search_onestop_flight` - Find one-stop flights
- `list_all_airports` - Get all available airports

**Booking Operations:**
- `book_reservation` - Create new flight bookings
- `cancel_reservation` - Cancel existing bookings
- `get_reservation_details` - Retrieve booking information

**Reservation Updates:**
- `update_reservation_flights` - Change flights in booking
- `update_reservation_passengers` - Modify passenger details
- `update_reservation_baggages` - Add checked bags

**Customer Service:**
- `get_user_details` - Look up customer information
- `send_certificate` - Issue compensation certificates
- `transfer_to_human_agents` - Escalate to human support

**Utilities:**
- `calculate` - Perform mathematical calculations
- `think` - Internal reasoning tool

## Usage in Notebooks

Both tutorial notebooks (07a and 07b) use these data files:

```python
import sys
sys.path.append('./data/ma-bench/')
sys.path.append('./data/tau-bench/')

# Import tools
from mabench.environments.airline.tools.book_reservation import book_reservation
# ... (13 more tool imports)

# Import airline policy
from tau_bench.envs.airline.wiki import WIKI

# Load test scenarios
with open('./data/tau-bench/tau_bench/envs/airline/tasks_singleturn.json', 'r') as f:
    tasks = json.load(f)
```

## Important Notes

1. **Package Initialization**: The `mabench/__init__.py` file is required for Python to recognize mabench as an importable package. Without it, you'll get `ModuleNotFoundError`.

2. **Dependencies**: These tools require the Strands framework and AWS Bedrock access. See the main `requirements.txt` for full dependencies.

3. **Independence**: This data directory makes tutorial 07 completely self-contained, with no dependencies on other tutorial folders.

## Citation

If you use these tools or datasets, please cite:

```
@article{tau-bench,
  title={τ-bench: A Benchmark for Tool-Augmented LLMs},
  year={2024},
  url={https://arxiv.org/abs/2406.12045}
}
```
