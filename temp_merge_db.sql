ATTACH 'data/posts.db' AS posts_db;
ATTACH 'data/comments.db' AS comments_db;

CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY,
            fetch_at TIMESTAMP,
            raw_data JSON
        ); 

INSERT OR IGNORE INTO posts
SELECT *
FROM posts_db.posts;

CREATE TABLE IF NOT EXISTS comments (
            comment_id TEXT PRIMARY KEY,
            post_id TEXT,
            fetch_at TIMESTAMP,
            raw_data JSON
        );

INSERT OR IGNORE INTO comments
SELECT *
FROM comments_db.comments;
