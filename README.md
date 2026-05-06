# Moltbook Post Analysis

Analysis workspace for data fetched by `moltbook-post-fetch`.

This repo reads a local SQLite database produced by the fetcher repo and uses
Python/Jupyter notebooks to explore, reshape, and export the data.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
