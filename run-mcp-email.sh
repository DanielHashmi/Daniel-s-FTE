#!/bin/bash
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"
source venv/bin/activate
export PYTHONPATH="/mnt/c/Users/kk/Desktop/Daniel's FTE"
exec python3 src/mcp/email_server.py
