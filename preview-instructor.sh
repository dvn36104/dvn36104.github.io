#!/bin/zsh
# Render and serve the INSTRUCTOR build (with final-exercise solutions)
# at http://localhost:8899 — never published, local only.
cd "$(dirname "$0")"
quarto render --profile instructor
pkill -f "http.server 8899" 2>/dev/null
(python3 -m http.server 8899 --directory _site-instructor >/dev/null 2>&1 &)
sleep 1
open http://localhost:8899
