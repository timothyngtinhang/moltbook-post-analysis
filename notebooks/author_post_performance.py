import numpy as np
import pandas as pd


def add_submolt_participation_label(author_features):
    df = author_features.copy()
    df["submolt_participation_label"] = np.select(
        [
            df["non_general_posts"].eq(0),
            df["non_general_post_share"].lt(0.25),
            df["non_general_post_share"].lt(0.75),
            df["non_general_post_share"].ge(0.75),
        ],
        [
            "General Only",
            "Mostly General",
            "Mixed Submolts",
            "Non-General Focused",
        ],
        default=pd.NA,
    )
    return df


def compute_post_level_engagement(posts, comments, post_submolts=None):
    post_cols = [
        "id",
        "author_id",
        "score",
        "upvotes",
        "downvotes",
        "comment_count",
    ]
    post_level = posts[[col for col in post_cols if col in posts.columns]].copy()
    post_level = post_level.rename(columns={"id": "post_id"})

    comment_counts = (
        comments.groupby("post_id", dropna=False)
        .agg(
            actual_comments=("id", "count"),
            unique_commenters=("author_id", "nunique"),
        )
        .reset_index()
    )
    post_level = post_level.merge(comment_counts, on="post_id", how="left")
    post_level[["actual_comments", "unique_commenters"]] = post_level[
        ["actual_comments", "unique_commenters"]
    ].fillna(0)

    if post_submolts is not None:
        post_level = post_level.merge(post_submolts, on="post_id", how="left")

    post_level["submolt_name"] = post_level.get("submolt_name", pd.Series(dtype=object))
    post_level["submolt_name"] = post_level["submolt_name"].fillna("unknown")
    post_level["is_general_submolt"] = post_level["submolt_name"].str.lower().eq("general")
    post_level["is_non_general_submolt"] = ~post_level["is_general_submolt"]
    return post_level


def _top_value(values):
    counts = pd.Series(values).dropna().value_counts()
    if counts.empty:
        return pd.NA
    return counts.index[0]


def _top_value_count(values):
    counts = pd.Series(values).dropna().value_counts()
    if counts.empty:
        return 0
    return int(counts.iloc[0])


def compute_author_post_performance_features(post_level):
    grouped = post_level.groupby("author_id", dropna=False)
    author_features = (
        grouped.agg(
            author_posts=("post_id", "count"),
            general_posts=("is_general_submolt", "sum"),
            non_general_posts=("is_non_general_submolt", "sum"),
            unique_submolts=("submolt_name", "nunique"),
            top_submolt=("submolt_name", _top_value),
            top_submolt_posts=("submolt_name", _top_value_count),
            post_score_total=("score", "sum"),
            post_score_mean=("score", "mean"),
            post_score_median=("score", "median"),
            post_upvotes_total=("upvotes", "sum"),
            post_upvotes_mean=("upvotes", "mean"),
            post_upvotes_median=("upvotes", "median"),
            post_comment_count_total=("comment_count", "sum"),
            post_comment_count_mean=("comment_count", "mean"),
            post_comment_count_median=("comment_count", "median"),
            post_actual_comments_total=("actual_comments", "sum"),
            post_actual_comments_mean=("actual_comments", "mean"),
            post_actual_comments_median=("actual_comments", "median"),
            post_unique_commenters_total=("unique_commenters", "sum"),
            post_unique_commenters_mean=("unique_commenters", "mean"),
            post_unique_commenters_median=("unique_commenters", "median"),
        )
        .reset_index()
    )
    author_features["non_general_post_share"] = (
        author_features["non_general_posts"] / author_features["author_posts"]
    )

    non_general = post_level[post_level["is_non_general_submolt"]].copy()
    if non_general.empty:
        non_general_features = pd.DataFrame(columns=["author_id"])
    else:
        non_general_features = (
            non_general.groupby("author_id", dropna=False)
            .agg(
                unique_non_general_submolts=("submolt_name", "nunique"),
                top_non_general_submolt=("submolt_name", _top_value),
                top_non_general_submolt_posts=("submolt_name", _top_value_count),
                non_general_score_median=("score", "median"),
                non_general_comment_count_median=("comment_count", "median"),
                non_general_unique_commenters_median=("unique_commenters", "median"),
            )
            .reset_index()
        )

    author_features = author_features.merge(
        non_general_features,
        on="author_id",
        how="left",
    )
    author_features["unique_non_general_submolts"] = author_features[
        "unique_non_general_submolts"
    ].fillna(0)
    author_features["top_non_general_submolt_posts"] = author_features[
        "top_non_general_submolt_posts"
    ].fillna(0)
    return add_submolt_participation_label(author_features)


def compute_author_submolt_performance(post_level):
    return (
        post_level.groupby(["author_id", "submolt_name"], dropna=False)
        .agg(
            posts=("post_id", "count"),
            score_total=("score", "sum"),
            score_median=("score", "median"),
            comment_count_total=("comment_count", "sum"),
            comment_count_median=("comment_count", "median"),
            unique_commenters_total=("unique_commenters", "sum"),
            unique_commenters_median=("unique_commenters", "median"),
        )
        .reset_index()
        .sort_values(["author_id", "posts"], ascending=[True, False])
    )


def compute_author_post_performance(posts, comments, post_submolts=None):
    post_level = compute_post_level_engagement(posts, comments, post_submolts)
    author_features = compute_author_post_performance_features(post_level)
    author_submolt = compute_author_submolt_performance(post_level)
    return author_features, author_submolt, post_level
