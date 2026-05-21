# Moltbook Post Analysis

Exploratory analysis of behavioral signatures in the Moltbook AI social network.

## Project overview

This project investigates behavioral patterns in Moltbook, an AI-only social network where autonomous or semi-autonomous agents post and comment. Rather than trying to interpret what the agents “believe” or “intend,” the analysis focuses on observable posting behavior: where authors post, how often they post, how regular their posting rhythm is, and whether they reuse similar text.

The project uses posts and comments from April 1–10, 2026. After cleaning and filtering, the main analysis focuses on non-minting authors with at least five posts, using author-level features for exploratory clustering.

## Main takeaway

The findings are modest but interpretable. The analysis does not uncover one dramatic hidden strategy or clear causal rule for gaining attention. Instead, it shows that Moltbook authors can be grouped into broad behavioral styles, including General-only posters, Submolt-only posters, high-volume mixed posters, low-volume mixed posters, and repetitive/recycled posters.

Posting location and volume appear more useful than timing regularity for separating author behavior. High-volume mixed posters reached the widest audience, but wider reach did not necessarily translate into the highest karma per post. A small repetitive-poster group showed near-identical repeated text and low engagement, suggesting that simple content recycling was detectable but not especially effective.

Overall, the project treats Moltbook as a noisy attention system shaped by platform mechanics, automation, and possible human influence. The value of the analysis is less about claiming a definitive theory of AI-agent behavior, and more about showing how interpretable behavioral features can be used to study activity patterns when semantic interpretation is risky.

## Repository contents

- `notebooks/` contains the analysis scripts used to generate tables and plots.
- `outputs/plots/` contains generated plot PDFs that are small enough to keep in git.
- `project_report_v1.pdf` is the full report export.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Expected Data

SQLite database files are not committed to this repository because they are too
large for git. You may download the source file from [Kaggle](https://www.kaggle.com/datasets/timothyngtinhang/moltbook-posts-and-comments-april-110-2026).

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
