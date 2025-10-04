"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import os

FOLDER_PATH = os.path.dirname(__file__)

with open(os.path.join(FOLDER_PATH, "wiki.md"), "r") as f:
    WIKI = f.read()
