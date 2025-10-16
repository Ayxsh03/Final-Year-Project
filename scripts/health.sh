#!/usr/bin/env bash
set -e
curl -sS http://localhost:3000/api/health | jq .
