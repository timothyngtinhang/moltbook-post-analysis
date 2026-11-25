# Moltbook Post Analysis

A Python project exploring how accounts on Moltbook, a social platform for AI agents, post and receive comments.

I wanted to see whether simple measures of posting activity could reveal useful patterns: how often accounts post, which communities they use, how regular their posting intervals are, and how much text they repeat.

The data covers posts from April 1–10, 2026, with comments retained within two days of each post. The clustering analysis uses authors with at least five posts after filtering out mint-transaction notes.

## What I built

- A data preparation and collection workflow in the companion [moltbook-post-fetch](https://github.com/timothyngtinhang/moltbook-post-fetch) repository, using Python and SQLite.
- Author-level features for posting volume, use of General versus other communities, variation in posting intervals, and average TF-IDF cosine similarity between posts.
- Gaussian mixture clustering on four features, with log transforms for posting counts and interval variability, followed by standardization.
- Plots and summaries comparing the groups' posting patterns, post scores, and numbers of distinct commenters.

## What I found

The five-group analysis separated accounts into broad patterns: General-only posters, posters using other communities, high- and low-volume mixed posters, and a small group with highly repetitive text.

High-volume mixed posters had the largest unique commenter reach in the analysis. The repetitive group had low observed engagement. These are descriptions of this sample; they do not show that a particular posting strategy causes better or worse engagement.

Here, **unique commenter reach** means the number of distinct other accounts that commented on an author's posts. It does not measure views or everyone who saw a post.

## Limits

This is a short snapshot of active accounts, not a representative sample of all Moltbook users. Accounts with fewer than five retained posts are excluded from clustering, and the cleaning step removes deleted content and deleted authors.

The current model uses **five components**. The script compares BIC across one to ten components, but then fixes the final count at five; it should not be read as an automatically BIC-selected result. Cluster labels are interpretations of the fitted groups, rather than verified account types.

The script also calculates account karma divided by sampled post count. Because account karma and the sampled posts can cover different periods, I would not use that ratio as a measure of karma earned per post in this study.

## Run the analysis

Requires Python and the packages in `requirements.txt`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Download the SQLite dataset from [Kaggle](https://www.kaggle.com/datasets/timothyngtinhang/moltbook-posts-and-comments-april-110-2026) and place it at `data/ready.db`. Database files are not included in this repository.

Then run from the repository root:

```bash
python notebooks/main_script.py
```

Plots are written to `outputs/plots/`. The collection and preparation scripts are in [moltbook-post-fetch](https://github.com/timothyngtinhang/moltbook-post-fetch).

## Files

| Path | Contents |
| --- | --- |
| `notebooks/` | Python analysis scripts |
| `outputs/plots/` | Exported plots |
| [project_report_v1.pdf](project_report_v1.pdf) | Original project report |
