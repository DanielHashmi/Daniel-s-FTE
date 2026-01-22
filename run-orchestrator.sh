#!/bin/bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
export PYTHONPATH="/mnt/c/Users/kk/Desktop/Daniel's FTE"
export PATH="/home/danielhashmi/.nvm/versions/node/v24.11.1/bin:$PATH"
exec ./venv/bin/python3 src/orchestration/orchestrator.py
