def highlight_posts_by_author_count(posts, min_posts=5):
    highlighted_posts = posts.copy()
    highlighted_posts["author_posts"] = highlighted_posts.groupby("author_id")[
        "id"
    ].transform("count")
    highlighted_posts["author_posts_ge_min"] = highlighted_posts["author_posts"] >= min_posts
    return highlighted_posts


def filter_posts_by_author_count(posts, min_posts=5):
    highlighted_posts = highlight_posts_by_author_count(posts, min_posts=min_posts)
    return highlighted_posts[highlighted_posts["author_posts_ge_min"]].copy()
