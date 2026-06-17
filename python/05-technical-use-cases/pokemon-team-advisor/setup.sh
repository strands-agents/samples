#!/bin/bash
# Downloads a subset of PokeAPI data for the demo (pokemon, moves, types).
# Run from this directory: ./setup.sh

set -e

echo "Cloning PokeAPI data (sparse checkout: pokemon, move, type)..."
git clone --depth 1 --filter=blob:none --sparse https://github.com/PokeAPI/api-data.git
cd api-data
git sparse-checkout set data/api/v2/pokemon data/api/v2/move data/api/v2/type
cd ..

# Symlink the data where the agent expects it
ln -sf api-data/data/api/v2 pokedata

# Create artifacts directory for offloaded content
mkdir -p artifacts

echo ""
echo "Done. $(du -sh pokedata | cut -f1) of Pokémon data ready."
echo "Run the agent: uv run demo_agent.py"
