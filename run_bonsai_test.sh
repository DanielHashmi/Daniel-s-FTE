#!/bin/bash
# Script to run ccr with claude and capture output

echo "Running: ccr code --print 'what is an apple?'"
echo "=========================================="
ccr code --print "what is an apple?" 2>&1
echo "=========================================="
echo "Exit code: $?"
