import numpy as np
import pandas as pd


POST_TIMING_STAT_COLS = [
    "post_gap_count",
    "post_mean_gap_minutes",
    "post_std_gap_minutes",
    "post_median_gap_minutes",
    "post_min_gap_minutes",
    "post_max_gap_minutes",
    "post_gap_cv",
]


def add_post_timing_labels(author_post_timing, min_posts=5):
    df = author_post_timing.copy()
    df.loc[df["posts"] < min_posts, POST_TIMING_STAT_COLS] = np.nan
    df["post_timing_label"] = np.select(
        [
            df["posts"] < min_posts,
            df["post_gap_cv"] < 0.3,
            df["post_gap_cv"].between(0.3, 0.5, inclusive="left"),
            df["post_gap_cv"].between(0.5, 1, inclusive="left"),
            df["post_gap_cv"].between(1, 2, inclusive="left"),
            df["post_gap_cv"] >= 2,
        ],
        [
            "Infrequent",
            "Very Regular",
            "Regular",
            "Mixed",
            "Irregular",
            "Very Irregular",
        ],
        default=pd.NA,
    )
    return df


def compute_author_post_timing(posts, authors=None, min_posts=5):
    post_events = (
        posts[["id", "author_id", "created_at"]]
        .dropna(subset=["author_id", "created_at"])
        .copy()
    )
    post_events["created_at"] = pd.to_datetime(
        post_events["created_at"],
        errors="coerce",
        utc=True,
    )
    post_events = (
        post_events
        .dropna(subset=["created_at"])
        .sort_values(["author_id", "created_at"])
    )

    post_events["gap_minutes"] = (
        post_events.groupby("author_id")["created_at"]
        .diff()
        .dt.total_seconds()
        .div(60)
    )

    post_counts = (
        post_events.groupby("author_id")
        .agg(
            posts=("id", "count"),
            first_post=("created_at", "min"),
            last_post=("created_at", "max"),
        )
        .reset_index()
    )

    post_gap_stats = (
        post_events.dropna(subset=["gap_minutes"])
        .groupby("author_id")
        .agg(
            post_gap_count=("gap_minutes", "count"),
            post_mean_gap_minutes=("gap_minutes", "mean"),
            post_std_gap_minutes=("gap_minutes", "std"),
            post_median_gap_minutes=("gap_minutes", "median"),
            post_min_gap_minutes=("gap_minutes", "min"),
            post_max_gap_minutes=("gap_minutes", "max"),
        )
        .reset_index()
    )

    author_post_timing = post_counts.merge(post_gap_stats, on="author_id", how="left")
    author_post_timing["post_gap_cv"] = (
        author_post_timing["post_std_gap_minutes"]
        / author_post_timing["post_mean_gap_minutes"]
    )
    author_post_timing = add_post_timing_labels(author_post_timing, min_posts=min_posts)

    if authors is not None:
        author_post_timing = author_post_timing.merge(
            authors,
            on="author_id",
            how="left",
        )

    return author_post_timing.sort_values(
        ["posts", "post_gap_cv"],
        ascending=[False, True],
    )


def post_cov_histogram_bins(author_post_timing, start=0, stop=5, step=0.1):
    post_cov = author_post_timing.loc[
        author_post_timing["post_gap_cv"].between(start, stop, inclusive="both"),
        "post_gap_cv",
    ].copy()

    bin_starts = np.round(np.arange(start, stop, step), 1)
    histogram = (
        np.minimum(np.floor(post_cov / step) * step, stop - step)
        .round(1)
        .value_counts()
        .reindex(bin_starts, fill_value=0)
        .rename_axis("cov_bin_start")
        .reset_index(name="authors")
    )
    histogram["cov_bin_end"] = (histogram["cov_bin_start"] + step).round(1)
    return histogram[["cov_bin_start", "cov_bin_end", "authors"]]
