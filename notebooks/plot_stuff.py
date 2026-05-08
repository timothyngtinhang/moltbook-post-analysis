
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def plot_4_distributions(
    GMM_data,
    feature_cols=None,
    feature_names=None,
    cluster_col=None,
    cluster_plot="overlap",
):
    if feature_cols is None:
        feature_cols = [
            col
            for col in GMM_data.select_dtypes(include="number").columns
            if col not in {"author_id", "cluster", "cluster_confidence"}
        ][:4]

    if len(feature_cols) != 4:
        raise ValueError(f"Expected exactly 4 feature columns, got {len(feature_cols)}: {feature_cols}")

    if feature_names is None:
        feature_names = {col: col for col in feature_cols}
    elif isinstance(feature_names, dict):
        feature_names = {col: feature_names.get(col, col) for col in feature_cols}
    else:
        if len(feature_names) != len(feature_cols):
            raise ValueError(
                f"Expected {len(feature_cols)} feature names, got {len(feature_names)}: {feature_names}"
            )
        feature_names = dict(zip(feature_cols, feature_names))

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(8, 6))
    axes = axes.flatten()

    for i, col in enumerate(feature_cols):
        feature_name = feature_names[col]
        plot_data = GMM_data[[col]].replace([np.inf, -np.inf], np.nan)

        if cluster_col is not None:
            plot_data[cluster_col] = GMM_data[cluster_col]
            plot_data = plot_data.dropna(subset=[col, cluster_col]).copy()
            plot_data[cluster_col] = plot_data[cluster_col].astype(int).astype(str)

            if cluster_plot == "overlap":
                sns.kdeplot(
                    data=plot_data,
                    x=col,
                    hue=cluster_col,
                    ax=axes[i],
                    fill=True,
                    alpha=0.18,
                    common_norm=False,
                    bw_adjust=0.7,
                    warn_singular=False,
                )
            elif cluster_plot == "contribution":
                sns.histplot(
                    data=plot_data,
                    x=col,
                    hue=cluster_col,
                    ax=axes[i],
                    bins=35,
                    stat="probability",
                    common_norm=True,
                    multiple="stack",
                    element="bars",
                    alpha=0.85,
                )
            else:
                raise ValueError("cluster_plot must be either 'overlap' or 'contribution'")
        else:
            values = plot_data[col].dropna()
            sns.kdeplot(
                x=values,
                ax=axes[i],
                fill=True,
                color="royalblue",
                bw_adjust=0.5,
            )

        # axes[i].set_title(feature_name)
        axes[i].set_xlabel(feature_name)
        axes[i].set_ylabel("Density")

    fig.tight_layout()
    return fig
