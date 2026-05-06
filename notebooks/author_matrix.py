import pandas as pd


def build_author_matrix(feature_frames, authors=None):
    frames = [frame.copy() for frame in feature_frames if frame is not None and not frame.empty]
    if not frames:
        return authors.copy() if authors is not None else pd.DataFrame()

    author_matrix = frames[0]
    for frame in frames[1:]:
        author_matrix = author_matrix.merge(frame, on="author_id", how="outer")

    if authors is not None:
        author_matrix = author_matrix.merge(authors, on="author_id", how="left")

    return author_matrix
