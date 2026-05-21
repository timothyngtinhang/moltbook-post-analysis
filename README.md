# Moltbook Post Analysis

Analysis workspace for the project **Investigating Behavioral Signatures in the
Moltbook AI Social Network**.

This project explores what behavioral strategies Moltbook agents use and
whether those strategies correspond to different engagement outcomes. The
analysis clusters post authors using a Gaussian Mixture Model over features such as
posting regularity, post text similarity, and posting volume across general and
non-general forums.

The data is collected and prepared with
[`moltbook-post-fetch`](https://github.com/timothyngtinhang/moltbook-post-fetch).
This repository focuses on the downstream analysis, plots, and report outputs.

## Repository contents

- `notebooks/` contains the analysis scripts used to generate tables and plots.
- `outputs/plots/` contains generated plot PDFs that are small enough to keep in git.
- `project_report_v1.pdf` is the current report export.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Expected Data

SQLite database files are not committed to this repository because they are too
large for git. Download `ready.db` from Kaggle:

<https://www.kaggle.com/datasets/timothyngtinhang/moltbook-posts-and-comments-april-110-2026>

The analysis expects `ready.db` to live under `data/`. With the Kaggle
CLI configured, download and unzip the dataset with:

```bash
cd moltbook-post-analysis
mkdir -p data
kaggle datasets download \
  -d timothyngtinhang/moltbook-posts-and-comments-april-110-2026 \
  -p data \
  --unzip
```

To use the Kaggle CLI, install it and create an API token from your Kaggle
account settings. Kaggle expects the token at `~/.kaggle/kaggle.json`.

After downloading, confirm the file is available at:

```text
data/ready.db
```

The fetch and preparation workflow that creates `ready.db` lives in
[`moltbook-post-fetch`](https://github.com/timothyngtinhang/moltbook-post-fetch).

## Run Analysis

The main analysis script expects `data/ready.db` to exist:

```bash
python notebooks/main_script.py
```

Generated plots are written to `outputs/plots/`. 
