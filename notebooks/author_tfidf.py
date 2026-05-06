import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _vectorize_texts(texts, **vectorizer_kwargs):
    vectorizer = TfidfVectorizer(**vectorizer_kwargs)
    return vectorizer.fit_transform(texts)


def remove_near_duplicate_texts(texts, cutoff=0.9, **vectorizer_kwargs):
    texts = pd.Series(texts).dropna().astype(str)
    texts = texts[texts.str.strip().ne("")]
    if len(texts) < 2:
        return texts, 0, 0.0

    try:
        matrix = _vectorize_texts(texts, **vectorizer_kwargs)
    except ValueError:
        return texts, 0, 0.0

    similarities = cosine_similarity(matrix)
    keep_positions = []
    removed_positions = []

    for position in range(len(texts)):
        if not keep_positions:
            keep_positions.append(position)
            continue

        max_similarity_to_kept = similarities[position, keep_positions].max()
        if max_similarity_to_kept > cutoff:
            removed_positions.append(position)
        else:
            keep_positions.append(position)

    filtered_texts = texts.iloc[keep_positions]
    removed_count = len(removed_positions)
    removed_share = removed_count / len(texts)
    return filtered_texts, removed_count, removed_share


def avg_cosine_similarity(corpus, min_posts=5, **vectorizer_kwargs):
    texts = pd.Series(corpus).dropna().astype(str)
    texts = texts[texts.str.strip().ne("")]
    if len(texts) < min_posts:
        return np.nan

    try:
        matrix = _vectorize_texts(texts, **vectorizer_kwargs)
    except ValueError:
        return np.nan

    similarities = cosine_similarity(matrix)
    upper_triangle = np.triu_indices_from(similarities, k=1)
    pairwise_similarities = similarities[upper_triangle]
    if len(pairwise_similarities) == 0:
        return np.nan

    return float(pairwise_similarities.mean())


def compute_author_post_tfidf_features(
    posts,
    text_col="title",
    fallback_text_col=None,
    min_posts=5,
    cutoff=0.9,
    analyzer="word",
    remove_near_duplicates=True,
):
    input_cols = ["author_id", text_col]
    if fallback_text_col is not None:
        input_cols.append(fallback_text_col)

    author_posts = posts[input_cols].dropna(subset=["author_id"]).copy()
    author_posts[text_col] = author_posts[text_col].fillna("").astype(str)
    if fallback_text_col is not None:
        fallback_text = author_posts[fallback_text_col].fillna("").astype(str)
        missing_text = author_posts[text_col].str.strip().eq("")
        author_posts.loc[missing_text, text_col] = fallback_text[missing_text]

    def author_similarity_features(texts):
        original_texts = pd.Series(texts).dropna().astype(str)
        original_texts = original_texts[original_texts.str.strip().ne("")]
        original_count = len(original_texts)

        if remove_near_duplicates:
            filtered_texts, removed_count, removed_share = remove_near_duplicate_texts(
                original_texts,
                cutoff=cutoff,
                analyzer=analyzer,
            )
        else:
            filtered_texts = original_texts
            removed_count = 0
            removed_share = 0.0

        return pd.Series(
            {
                "post_text_original_posts": original_count,
                "post_text_posts": len(filtered_texts),
                "post_text_near_duplicate_removed_posts": removed_count,
                "post_text_near_duplicate_removed_share": removed_share,
                "post_text_avg_cosine_similarity": avg_cosine_similarity(
                    filtered_texts,
                    min_posts=min_posts,
                    analyzer=analyzer,
                ),
            }
        )

    features = (
        author_posts.groupby("author_id", dropna=False)[text_col]
        .apply(author_similarity_features)
        .unstack()
        .reset_index()
    )

    return features
