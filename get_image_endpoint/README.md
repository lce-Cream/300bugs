# Install UV
https://docs.astral.sh/uv/getting-started/installation/

# Install deps
uv sync

# Activate venv
source .venv/bin/activate

# Start it
uvicorn get_image:app --reload

# Use it
open index.html in your browser