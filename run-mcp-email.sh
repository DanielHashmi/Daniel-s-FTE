#!/bin/bash
cd "$(dirname "$0")"
export PATH=$PATH:/usr/local/bin
cd mcp-servers/email-mcp
npm start