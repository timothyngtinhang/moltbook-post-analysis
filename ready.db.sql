BEGIN TRANSACTION;

DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS comment_authors;
DROP TABLE IF EXISTS post_authors;
DROP TABLE IF EXISTS post_submolts;

CREATE TABLE "comment_authors" (
	"fetch_at"	DATETIME,
	"id"	TEXT,
	"name"	TEXT,
	"description"	TEXT,
	"avatar_url"	TEXT,
	"karma"	REAL,
	"follower_count"	REAL,
	"following_count"	REAL,
	"is_claimed"	INTEGER,
	"is_active"	INTEGER,
	"created_at"	TEXT,
	"last_active"	DATETIME,
	"deleted_at"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE "comments" (
	"fetch_at"	DATETIME,
	"id"	TEXT,
	"post_id"	TEXT,
	"content"	TEXT,
	"author_id"	TEXT,
	"upvotes"	INTEGER,
	"downvotes"	INTEGER,
	"score"	INTEGER,
	"reply_count"	INTEGER,
	"is_deleted"	INTEGER,
	"depth"	INTEGER,
	"verification_status"	TEXT,
	"is_spam"	INTEGER,
	"created_at"	DATETIME,
	"updated_at"	DATETIME,
	"parent_id"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE "post_authors" (
	"fetch_at"	DATETIME,
	"id"	TEXT,
	"name"	TEXT,
	"description"	TEXT,
	"avatar_url"	TEXT,
	"karma"	REAL,
	"follower_count"	REAL,
	"following_count"	REAL,
	"is_claimed"	INTEGER,
	"is_active"	INTEGER,
	"created_at"	TEXT,
	"last_active"	DATETIME,
	"deleted_at"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE "post_submolts" (
	"fetch_at"	DATETIME,
	"id"	TEXT,
	"name"	TEXT,
	"display_name"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE "posts" (
	"fetch_at"	DATETIME,
	"id"	TEXT,
	"title"	TEXT,
	"content"	TEXT,
	"type"	TEXT,
	"author_id"	TEXT,
	"upvotes"	INTEGER,
	"downvotes"	INTEGER,
	"score"	INTEGER,
	"comment_count"	INTEGER,
	"hot_score"	INTEGER,
	"is_pinned"	INTEGER,
	"is_locked"	INTEGER,
	"is_deleted"	INTEGER,
	"verification_status"	TEXT,
	"is_spam"	INTEGER,
	"created_at"	DATETIME,
	"updated_at"	DATETIME,
	"url"	TEXT,
	PRIMARY KEY("id")
);
COMMIT;

-- 1. Link the data source
ATTACH DATABASE '/Users/timo0305/Github/moltbook-post-analysis/data/ready.db' AS ready;

-- 2. Move data into your already-created schema
-- (Assuming column names match)
INSERT INTO comment_authors SELECT * FROM ready.comment_authors;
INSERT INTO comments SELECT * FROM ready.comments;
INSERT INTO post_authors SELECT * FROM ready.post_authors;
INSERT INTO post_submolts SELECT * FROM ready.post_submolts;
INSERT INTO posts SELECT * FROM ready.posts;

-- 3. Cleanup
DETACH DATABASE ready;
