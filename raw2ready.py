from pathlib import Path

import json
import sqlite3

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DB_PATH = PROJECT_ROOT / 'data' / 'raw.db'
READY_DB_PATH = PROJECT_ROOT / 'data' / 'ready.db'

AUTHOR_COLUMN_RENAME = {
    'avatarUrl': 'avatar_url',
    'followerCount': 'follower_count',
    'followingCount': 'following_count',
    'isClaimed': 'is_claimed',
    'isActive': 'is_active',
    'createdAt': 'created_at',
    'lastActive': 'last_active',
    'deletedAt': 'deleted_at',
}

AUTHOR_COLUMNS = [
    'fetch_at',
    'id',
    'name',
    'description',
    'avatar_url',
    'karma',
    'follower_count',
    'following_count',
    'is_claimed',
    'is_active',
    'created_at',
    'last_active',
    'deleted_at',
]


def load_raw_data():
    with sqlite3.connect(RAW_DB_PATH) as conn:
        df_comments = pd.read_sql('select * from comments', conn)
        df_posts = pd.read_sql('select * from posts', conn)

    return df_comments, df_posts


def normalize_author_columns(df):
    return df.rename(columns=AUTHOR_COLUMN_RENAME).reindex(columns=AUTHOR_COLUMNS)


def json_expanded(type: str, df: pd.DataFrame):
    if type == 'comments':
        return pd.concat(
            [
                df.drop(['comment_id', 'post_id', 'raw_data'], axis=1),
                pd.json_normalize(df['raw_data'].apply(json.loads), max_level=0)
            ],
            axis=1
        )

    if type == 'posts':
        nested_posts = df['raw_data'].apply(json.loads).apply(lambda x: x['post'])
        return pd.concat(
            [
                df['fetch_at'],
                pd.json_normalize(nested_posts, max_level=0)
            ],
            axis=1
        )

    raise ValueError("Type must be either 'comments' or 'posts'")


def _get_next_reply_level(df):
    df = df.copy()
    mask = df['replies'].str.len() > 0

    if not any(mask):
        return pd.DataFrame()

    exploded = df.loc[mask, ['fetch_at', 'replies']].explode('replies')
    nested_df = pd.json_normalize(exploded['replies'], max_level=0)

    return pd.concat(
        [
            exploded.reset_index(drop=True).drop('replies', axis=1),
            nested_df.reset_index(drop=True)
        ],
        axis=1
    )


def expand_all_replies(df_json_expanded, max_depth=10):
    df_list = [df_json_expanded]
    df = df_json_expanded

    for depth in range(max_depth):
        df_next_depth = _get_next_reply_level(df)
        if df_next_depth.empty:
            break

        df_list.append(df_next_depth)
        df = df_next_depth
        print(f"Depth {depth + 1} has {len(df_next_depth)} comments")

    return pd.concat(df_list, ignore_index=True)


def extract_unique_json_from_field(field_name: str, df: pd.DataFrame) -> pd.DataFrame:
    expanded_df = df[field_name].apply(pd.Series)
    timed_expanded_df = pd.concat([df['fetch_at'], expanded_df], axis=1)

    return (
        timed_expanded_df
        .sort_values('fetch_at', ascending=False)
        .drop_duplicates(subset='id')
    )


def is_deleted_status(df_entries):
    if 'is_deleted' not in df_entries.columns:
        return pd.Series(False, index=df_entries.index)

    is_deleted = df_entries['is_deleted'].fillna(False)

    if pd.api.types.is_bool_dtype(is_deleted):
        return is_deleted

    if pd.api.types.is_numeric_dtype(is_deleted):
        return is_deleted.astype(int).astype(bool)

    return is_deleted.astype(str).str.lower().isin(['true', '1', 't', 'yes'])


def remove_entries_with_deleted_status(df_entries, kind):
    retained_entries = df_entries[~is_deleted_status(df_entries)]

    print(f'excluded {len(df_entries) - len(retained_entries)} deleted {kind}')
    print(f'retained {len(retained_entries)} {kind}')

    return retained_entries


def filter_comments_within_2days(df_unnested_comments, df_clean_posts):
    count_within_2_days = duckdb.sql('''
        select count(*)
        from df_unnested_comments c
        join df_clean_posts p
            on p.id = c.post_id
        where cast(c.created_at as timestamptz)
            between cast(p.created_at as timestamptz)
            and cast(p.created_at as timestamptz) + interval '2 days'
    ''').fetchone()[0]

    count_not_within_2_days = duckdb.sql('''
        select count(*)
        from df_unnested_comments c
        join df_clean_posts p
            on p.id = c.post_id
        where cast(c.created_at as timestamptz)
            not between cast(p.created_at as timestamptz)
            and cast(p.created_at as timestamptz) + interval '2 days'
    ''').fetchone()[0]

    id_within_2days_comment = duckdb.sql('''
        select c.id
        from df_unnested_comments c
        join df_clean_posts p
            on p.id = c.post_id
        where cast(c.created_at as timestamptz)
            between cast(p.created_at as timestamptz)
            and cast(p.created_at as timestamptz) + interval '2 days'
    ''').df()['id']

    print(f'excluded {count_not_within_2_days} comments > 2 days of post creation')
    print(f'retained {count_within_2_days} comments <= 2 days of post creation')

    return df_unnested_comments[
        df_unnested_comments['id'].isin(id_within_2days_comment)
    ]


def remove_deleted_authors(df, df_unique_author, kind):
    deleted_author_mask = (
        df_unique_author['deleted_at'].notna()
        & (df_unique_author['deleted_at'].astype(str).str.strip() != '')
    )
    deleted_author_ids = df_unique_author.loc[deleted_author_mask, 'id']

    df_retained_author = df_unique_author[
        ~df_unique_author['id'].isin(deleted_author_ids)
    ]
    df_retained = df[~df['author_id'].isin(deleted_author_ids)]

    print(f'excluded {len(deleted_author_ids)} deleted unique authors from {kind}')
    print(f'retained {len(df_retained_author)} unique authors from {kind}')
    print(f'excluded {len(df) - len(df_retained)} {kind} by deleted authors')
    print(f'retained {len(df_retained)} {kind}')

    return df_retained, df_retained_author


def prepare_posts(df_posts):
    posts_expanded = json_expanded('posts', df_posts)
    posts_not_deleted = remove_entries_with_deleted_status(posts_expanded, 'posts')

    post_authors_raw = extract_unique_json_from_field(
        field_name='author',
        df=posts_not_deleted
    )
    post_authors = normalize_author_columns(post_authors_raw)

    posts_retained, post_authors_retained = remove_deleted_authors(
        posts_not_deleted,
        post_authors,
        'posts'
    )

    post_submolts = extract_unique_json_from_field(
        field_name='submolt',
        df=posts_retained
    )

    posts_clean = posts_retained.drop(columns=['submolt', 'author'])

    return posts_clean, post_authors_retained, post_submolts


def prepare_comments(df_comments, posts_clean):
    comments_expanded = json_expanded('comments', df_comments)
    comments_unnested = expand_all_replies(comments_expanded, max_depth=5)

    comments_not_deleted = remove_entries_with_deleted_status(
        comments_unnested,
        'comments'
    )
    comments_recent = filter_comments_within_2days(
        comments_not_deleted,
        posts_clean
    )

    comment_authors_raw = extract_unique_json_from_field(
        field_name='author',
        df=comments_recent
    )
    comment_authors = normalize_author_columns(comment_authors_raw)

    comments_clean, comment_authors_clean = remove_deleted_authors(
        comments_recent,
        comment_authors,
        'comments'
    )
    comments_clean = comments_clean.drop(columns=['replies', 'author'])

    return comments_clean, comment_authors_clean


def write_ready_data(
    posts_clean,
    comments_clean,
    post_authors_clean,
    comment_authors_clean,
    post_submolts
):
    with sqlite3.connect(READY_DB_PATH) as conn:
        comments_clean.to_sql(
            name='comments',
            con=conn,
            index=False,
            if_exists='replace'
        )
        comment_authors_clean.to_sql(
            name='comment_authors',
            con=conn,
            index=False,
            if_exists='replace'
        )
        posts_clean.to_sql(
            name='posts',
            con=conn,
            index=False,
            if_exists='replace'
        )
        post_authors_clean.to_sql(
            name='post_authors',
            con=conn,
            index=False,
            if_exists='replace'
        )
        post_submolts.to_sql(
            name='post_submolts',
            con=conn,
            index=False,
            if_exists='replace'
        )


def main():
    df_comments, df_posts = load_raw_data()

    posts_clean, post_authors_clean, post_submolts = prepare_posts(df_posts)
    comments_clean, comment_authors_clean = prepare_comments(
        df_comments,
        posts_clean
    )

    write_ready_data(
        posts_clean,
        comments_clean,
        post_authors_clean,
        comment_authors_clean,
        post_submolts
    )


if __name__ == "__main__":
    main()
