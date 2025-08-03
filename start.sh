#!/bin/bash

set -e  # Exit on any error

# Run embedding preprocessing
python embeddings.py

# Start FastAPI in background
python api.py &

# Start Streamlit in foreground
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
