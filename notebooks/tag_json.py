import json
import re

import pandas as pd


# Finds simple/flat JSON-ish snippets. This intentionally ignores nested JSON.
JSON_RE = re.compile(r"\{[^{}]+\}")


def get_json_objects(text):
    if not isinstance(text, str):
        return []

    json_objects = []
    for match in JSON_RE.findall(text):
        try:
            obj = json.loads(match)
        except json.JSONDecodeError:
            continue

        if isinstance(obj, dict):
            json_objects.append(obj)

    return json_objects


def has_json_like(text):
    return bool(get_json_objects(text))


def is_mint_transaction_note(text):
    for obj in get_json_objects(text):
        keys = set(obj.keys())
        if {"op", "tick", "amt", "p"}.issubset(keys):
            return True
    return False


def add_json_tags(df, content_col="content"):
    df = df.drop(
        columns=[
            "is_mint_transaction_note",
            "is_other_json_like",
        ],
        errors="ignore",
    ).copy()

    df["is_mint_transaction_note"] = df[content_col].apply(is_mint_transaction_note)
    df["is_other_json_like"] = (
        df[content_col].apply(has_json_like) & ~df["is_mint_transaction_note"]
    )

    # SQLite-friendly 0/1 flags.
    df["is_mint_transaction_note"] = df["is_mint_transaction_note"].astype(int)
    df["is_other_json_like"] = df["is_other_json_like"].astype(int)

    return df


def json_tag_summary(posts, comments):
    return pd.DataFrame(
        [
            {
                "table": "posts",
                "rows": len(posts),
                "mint_transaction_notes": posts["is_mint_transaction_note"].sum(),
                "other_json_like": posts["is_other_json_like"].sum(),
            },
            {
                "table": "comments",
                "rows": len(comments),
                "mint_transaction_notes": comments["is_mint_transaction_note"].sum(),
                "other_json_like": comments["is_other_json_like"].sum(),
            },
        ]
    )


def filter_mint_transaction_notes(
    posts,
    comments=None,
    remove_comments_on_mint_posts=True,
):
    post_mint_mask = posts["is_mint_transaction_note"].eq(1)
    filtered_posts = posts.loc[~post_mint_mask].copy()

    if comments is None:
        return filtered_posts

    comment_mint_mask = comments["is_mint_transaction_note"].eq(1)

    if remove_comments_on_mint_posts:
        comment_mint_mask = comment_mint_mask | comments["post_id"].isin(
            posts.loc[post_mint_mask, "id"]
        )

    filtered_comments = comments.loc[~comment_mint_mask].copy()
    return filtered_posts, filtered_comments


def mint_filter_summary(posts_before, comments_before, posts_after, comments_after):
    return pd.DataFrame(
        [
            {
                "table": "posts",
                "before": len(posts_before),
                "removed": len(posts_before) - len(posts_after),
                "after": len(posts_after),
            },
            {
                "table": "comments",
                "before": len(comments_before),
                "removed": len(comments_before) - len(comments_after),
                "after": len(comments_after),
            },
        ]
    )


add_json_spam_flags = add_json_tags
json_spam_summary = json_tag_summary
filter_spam_mint = filter_mint_transaction_notes
