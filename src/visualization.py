"""Map and plotting utilities for the project."""
import matplotlib.pyplot as plt


def quick_map(ax=None, **kwargs):
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    return ax
