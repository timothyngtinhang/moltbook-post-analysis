#%%
import pandas as pd
import sqlite3
from pathlib import Path
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture
import matplotlib.pyplot as plt
import seaborn as sns

from tag_json import (
    add_json_tags,
    filter_mint_transaction_notes,
    json_tag_summary,
    mint_filter_summary,
)
from author_matrix import build_author_matrix
from post_cov import compute_author_post_timing, post_cov_histogram_bins
from author_tfidf import compute_author_post_tfidf_features

from author_post_performance import compute_author_post_performance
from author_post_threshold import (
    filter_posts_by_author_count,
    highlight_posts_by_author_count,
)

#%%

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "ready.db"
OUTPUT_PLOT_DIR = OUTPUT_TABLE_DIR = PROJECT_ROOT / "outputs" / "tables"
OUTPUT_TABLE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PLOT_DIR = PROJECT_ROOT / "outputs" / "plots"
OUTPUT_PLOT_DIR.mkdir(parents=True, exist_ok=True)
 
with sqlite3.connect(DB_PATH) as conn:
    comments = pd.read_sql('select * from comments', conn)
    posts = pd.read_sql('select * from posts', conn)
    authors = pd.read_sql(
        """
        select id as author_id, name, max(karma) as karma, max(follower_count) as follower_count
        from (
            select id, name, karma, follower_count from post_authors
            union all
            select id, name, karma, follower_count from comment_authors
        )
        group by id, name
        """,
        conn,
    )
    post_submolts = pd.read_sql(
        """
        select
            id as post_id,
            submolt_name
        from posts
        """,
        conn,
    )

#%%
# Step 1: Removing mint-note posts and comments with Regex
posts_tagged = add_json_tags(posts)
comments_tagged = add_json_tags(comments)

json_tag_counts = json_tag_summary(posts_tagged, comments_tagged)
json_tag_counts

posts, comments = filter_mint_transaction_notes(posts_tagged, comments_tagged)
mint_filter_summary(posts_tagged, comments_tagged, posts, comments)

# %% 

posts["created_at"] = pd.to_datetime(posts["created_at"], errors="coerce", utc=True)
comments["created_at"] = pd.to_datetime(comments["created_at"], errors="coerce", utc=True)

#%% selecting only posts with author posting >= 5
highlighted_posts = highlight_posts_by_author_count(posts, min_posts=5)
posts_from_5_post_authors = filter_posts_by_author_count(posts, min_posts=5)

print(f'remove posts from author where min posts < 5  {len(highlighted_posts) - len(posts_from_5_post_authors)}')
print(f'posts remaining: {len(posts_from_5_post_authors)}')

removed_author_count = highlighted_posts["author_id"].nunique() - posts_from_5_post_authors["author_id"].nunique()
remaining_author_count = posts_from_5_post_authors["author_id"].nunique()
print(f'removing unique author  {removed_author_count}')
print(f'unique author remaining {remaining_author_count}')

posts=posts_from_5_post_authors

# %% plot submolt
submolt_counts = post_submolts["submolt_name"].value_counts()
plot_counts = pd.concat([
    submolt_counts.head(7),
    pd.Series({"Other": submolt_counts.iloc[7:].sum()})
])

ax = plot_counts.plot(kind="bar", figsize=(5, 3), color="0.45")
ax.set_title("Posts are dispersed across many submolts")
ax.set_xlabel("")
ax.set_ylabel("Posts")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(OUTPUT_PLOT_DIR / 'submolt distribution.pdf',bbox_inches='tight')
plt.show()
# %% calculate the behavioral sigiture (CoV, Similarity)
author_post_timing = compute_author_post_timing(posts, min_posts=5)
author_post_tfidf = compute_author_post_tfidf_features(
    posts,
    text_col="content",
    min_posts=5,
    cutoff=0.9,
    remove_near_duplicates=False,
)
print("Near-duplicate content removal setting: disabled")

#%% plot regularity CoV
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

timing_labels = [
    "Very Regular",
    "Regular",
    "Mixed",
    "Irregular",
    "Very Irregular",
]
timing_display_labels = [
    "Very regular\nCoV < 0.3",
    "Regular\n(0.3-0.5)",
    "Mixed\n(0.5-1.0)",
    "Irregular\n(1.0-2.0)",
    "Very irregular\nCoV > 2.0",
]
timing_colors = ["#3f6f82", "#6f9bb0", "#8c959e", "#ff9659", "#bd5a62"]

cov_category = (
    author_post_timing["post_timing_label"]
    .value_counts()
    .reindex(timing_labels, fill_value=0)
)
cov_percent = cov_category / cov_category.sum()

fig, ax = plt.subplots(figsize=(9.5, 6.2), dpi=130)
bars = ax.bar(
    timing_display_labels,
    cov_category.values,
    color=timing_colors,
    edgecolor="#555555",
    linewidth=0.4,
)

for bar, pct in zip(bars, cov_percent):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + cov_category.max() * 0.018,
        f"{pct:.1%}",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#333333",
    )

ax.axvline(1.5, color="#777777", linestyle="--", linewidth=1.1, alpha=0.65)

ax.set_ylabel("Number of authors", fontsize=12)
ax.set_xlabel("")
ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("{x:,.0f}"))
ax.tick_params(axis="x", labelsize=10)
ax.tick_params(axis="y", labelsize=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.8)
ax.spines["bottom"].set_linewidth(0.8)
ax.grid(axis="y", color="#dddddd", linewidth=0.6, alpha=0.5)
ax.set_axisbelow(True)
ax.set_ylim(0, cov_category.max() * 1.15)
fig.tight_layout()
fig.savefig(OUTPUT_PLOT_DIR / "post_timing_cov_classification.pdf", bbox_inches="tight")
plt.show()
#%% prepare data for GMM

author_post_performance, author_submolt_performance, post_level_engagement = (
    compute_author_post_performance(posts, comments, post_submolts=post_submolts)
)
post_author_lookup = posts[["id", "author_id"]].rename(
    columns={"id": "post_id", "author_id": "post_author_id"}
)
author_commenter_reach = (
    comments[["post_id", "author_id"]]
    .rename(columns={"author_id": "commenter_author_id"})
    .merge(post_author_lookup, on="post_id", how="inner")
)
author_commenter_reach = author_commenter_reach[
    author_commenter_reach["commenter_author_id"].notna()
    & author_commenter_reach["post_author_id"].notna()
    & author_commenter_reach["commenter_author_id"].ne(
        author_commenter_reach["post_author_id"]
    )
]
author_commenter_reach = (
    author_commenter_reach.groupby("post_author_id", dropna=False)
    .agg(total_unique_commenter_reach=("commenter_author_id", "nunique"))
    .reset_index()
    .rename(columns={"post_author_id": "author_id"})
)
author_post_performance = author_post_performance.merge(
    author_commenter_reach,
    on="author_id",
    how="left",
)
author_post_performance["total_unique_commenter_reach"] = author_post_performance[
    "total_unique_commenter_reach"
].fillna(0)
post_cov_histogram = post_cov_histogram_bins(author_post_timing)
author_feature_matrix = build_author_matrix(
    [
        author_post_timing,
        author_post_performance,
        author_post_tfidf,
    ],
    authors=authors,
)

GMM_prep = author_feature_matrix[['author_id', 'post_gap_cv', 'general_posts', 'non_general_posts', 'post_text_avg_cosine_similarity']]

# %% plot GMM features
import numpy as np
from plot_stuff import plot_4_distributions

distribution_feature_names = {
    "post_gap_cv": "Post Timing Variability",
    "general_posts": "General Posts",
    "non_general_posts": "Non-General Posts",
    "post_text_avg_cosine_similarity": "Average Post Text Similarity",
}

fig = plot_4_distributions(GMM_prep, feature_names=distribution_feature_names)
fig.savefig(OUTPUT_PLOT_DIR /'raw feature distributions.pdf', bbox_inches='tight')
fig.show()
#%% plot GMM log feature

GMM_prep_transformed = GMM_prep[['author_id']].copy()
GMM_prep_transformed['log_post_gap_cv'] = np.log1p(GMM_prep['post_gap_cv'])
GMM_prep_transformed['log_non_general_posts'] = np.log1p(GMM_prep['non_general_posts'])
GMM_prep_transformed['log_general_posts'] = np.log1p(GMM_prep['general_posts'])
GMM_prep_transformed['post_text_avg_cosine_similarity'] = GMM_prep['post_text_avg_cosine_similarity']

transformed_distribution_feature_names = {
    "log_post_gap_cv": "Log Post Timing Variability",
    "log_non_general_posts": "Log Non-General Posts",
    "log_general_posts": "Log General Posts",
    "post_text_avg_cosine_similarity": "Average Post Text Similarity",
}

fig = plot_4_distributions(GMM_prep_transformed, feature_names=transformed_distribution_feature_names)
fig.savefig(OUTPUT_PLOT_DIR /'transformed feature distributions.pdf', bbox_inches='tight')
fig.show()
# %% do GMM, find optimal K

feature_cols = [
    "log_post_gap_cv",
    "log_non_general_posts",
    "log_general_posts",
    "post_text_avg_cosine_similarity",
]

scaler = StandardScaler()
model_data = GMM_prep_transformed[feature_cols].replace([np.inf, -np.inf], np.nan)
missing_feature_summary = model_data.isna().sum()
print("Missing values before GMM scaling:")
print(missing_feature_summary[missing_feature_summary > 0])

model_data = model_data.dropna()
print(f"Rows used for GMM: {len(model_data)} / {len(GMM_prep_transformed)}")

scaled_data = scaler.fit_transform(model_data)

component_range = range(1, 11)
bic_results = []

for n_components in component_range:
    gmm = GaussianMixture(
        n_components=n_components,
        covariance_type="full",
        n_init=10,
        random_state=6740,
    )
    gmm.fit(scaled_data)
    bic_results.append(
        {
            "n_components": n_components,
            "bic": gmm.bic(scaled_data),
            "aic": gmm.aic(scaled_data),
        }
    )

bic_results = pd.DataFrame(bic_results)
best_n_components = int(bic_results.loc[bic_results["bic"].idxmin(), "n_components"])
best_n_components = 5

best_gmm = GaussianMixture(
    n_components=best_n_components,
    covariance_type="full",
    n_init=10,
    random_state=6740,
)
clusters = best_gmm.fit_predict(scaled_data)
cluster_probabilities = best_gmm.predict_proba(scaled_data)

GMM_prep_transformed["cluster"] = np.nan
GMM_prep_transformed["cluster_confidence"] = np.nan
GMM_prep_transformed.loc[model_data.index, "cluster"] = clusters
GMM_prep_transformed.loc[model_data.index, "cluster_confidence"] = cluster_probabilities.max(axis=1)
GMM_prep_transformed["cluster"] = GMM_prep_transformed["cluster"].astype("Int64")

gmm_author_assignments = (
    author_feature_matrix.merge(
        GMM_prep_transformed[
            [
                "author_id",
                "log_post_gap_cv",
                "log_non_general_posts",
                "log_general_posts",
                "post_text_avg_cosine_similarity",
                "cluster",
                "cluster_confidence",
            ]
        ],
        on="author_id",
        how="left",
        suffixes=("", "_model"),
    )
    .rename(columns={"cluster": "gmm_cluster"})
)
gmm_author_assignments["gmm_cluster_label"] = gmm_author_assignments[
    "gmm_cluster"
].apply(lambda value: pd.NA if pd.isna(value) else f"cluster_{int(value)}")
gmm_author_assignments["account_karma_per_post"] = (
    gmm_author_assignments["karma"] / gmm_author_assignments["author_posts"]
)

gmm_author_assignment_cols = [
    "author_id",
    "name",
    "gmm_cluster",
    "gmm_cluster_label",
    "cluster_confidence",
    "post_gap_cv",
    "general_posts",
    "non_general_posts",
    "post_text_avg_cosine_similarity",
    "log_post_gap_cv",
    "log_general_posts",
    "log_non_general_posts",
    "author_posts",
    "post_score_mean",
    "post_score_total",
    "post_unique_commenters_total",
    "post_unique_commenters_mean",
    "total_unique_commenter_reach",
    "karma",
    "account_karma_per_post",
    "follower_count",
]
gmm_author_assignments = gmm_author_assignments[
    [col for col in gmm_author_assignment_cols if col in gmm_author_assignments.columns]
]

gmm_cluster_summary = (
    gmm_author_assignments.dropna(subset=["gmm_cluster"])
    .groupby(["gmm_cluster", "gmm_cluster_label"], dropna=False)
    .agg(
        authors=("author_id", "nunique"),
        mean_cluster_confidence=("cluster_confidence", "mean"),
        mean_post_gap_cv=("post_gap_cv", "mean"),
        mean_general_posts=("general_posts", "mean"),
        mean_non_general_posts=("non_general_posts", "mean"),
        mean_post_text_avg_cosine_similarity=(
            "post_text_avg_cosine_similarity",
            "mean",
        ),
        median_post_gap_cv=("post_gap_cv", "median"),
        median_general_posts=("general_posts", "median"),
        median_non_general_posts=("non_general_posts", "median"),
        median_post_text_avg_cosine_similarity=(
            "post_text_avg_cosine_similarity",
            "median",
        ),
        mean_author_posts=("author_posts", "mean"),
        mean_post_score=("post_score_mean", "mean"),
        median_post_score=("post_score_mean", "median"),
        mean_total_post_score=("post_score_total", "mean"),
        mean_post_unique_commenters_total=("post_unique_commenters_total", "mean"),
        mean_post_unique_commenters=("post_unique_commenters_mean", "mean"),
        mean_total_unique_commenter_reach=("total_unique_commenter_reach", "mean"),
        median_total_unique_commenter_reach=("total_unique_commenter_reach", "median"),
        mean_author_karma=("karma", "mean"),
        median_author_karma=("karma", "median"),
        mean_account_karma_per_post=("account_karma_per_post", "mean"),
        median_account_karma_per_post=("account_karma_per_post", "median"),
    )
    .reset_index()
    .sort_values("authors", ascending=False)
)

print(f"Best GMM component count by BIC: {best_n_components}")
bic_results

# %% plot GMM alignment 
fig = plot_4_distributions(
    GMM_prep_transformed,
    feature_cols=feature_cols,
    feature_names=transformed_distribution_feature_names,
    cluster_col="cluster",
    cluster_plot="contribution",
)
fig.savefig(OUTPUT_PLOT_DIR / 'contributions of cluster to features.pdf', bbox_inches='tight')
fig.show()

# %% plot BIC
fig, ax = plt.subplots(figsize=(8, 5))
sns.lineplot(
    data=bic_results,
    x="n_components",
    y="bic",
    marker="o",
    ax=ax,
)
ax.axvline(best_n_components, color="crimson", linestyle="--", label=f"Choose k = {best_n_components}")
ax.set_title("GMM BIC by Component Count")
ax.set_xlabel("Number of Components")
ax.set_ylabel("BIC")
ax.legend()
fig.tight_layout()
fig.savefig(
    OUTPUT_PLOT_DIR / "GMM component BIC.pdf",
    bbox_inches="tight",)
plt.show()


#%% GMM summary
gmm_asg = gmm_cluster_summary[['gmm_cluster', 'authors','median_post_gap_cv'
,'mean_general_posts','mean_non_general_posts','median_post_text_avg_cosine_similarity', 'mean_post_score', 'median_post_score'
,'mean_total_unique_commenter_reach']].sort_values('gmm_cluster').reset_index(drop=True)

gmm_latex = gmm_asg.set_index("gmm_cluster").T
gmm_latex.columns = [f"gmm_cluster {col}" for col in gmm_latex.columns]
gmm_latex.index.name = "Metric"

print(gmm_latex.to_latex(float_format="%.2f"))
