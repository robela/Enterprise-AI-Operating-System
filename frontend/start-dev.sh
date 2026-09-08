#!/bin/bash
cd "$(dirname "$0")"
rm -rf node_modules
npm install --force
npm run dev -- -p 3001
