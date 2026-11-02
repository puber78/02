"""Global alignment must keep a skipped item / duplicate photo local."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from import_captures import align_photos  # noqa: E402


def _score_map(pairs):
    """Return a score_pair closure from an explicit {(i, k): score} map."""
    table = dict(pairs)

    def score_pair(i, k):
        return table.get((i, k), 0.0)

    return score_pair


def test_alignment_without_gaps_is_identity():
    items, files = list(range(6)), list(range(6))
    assign = align_photos(items, files, _score_map({(i, i): 400.0 for i in range(6)}))
    assert assign == {i: i for i in range(6)}


def test_skipped_item_does_not_shift_the_rest():
    # item 2 was skipped by the operator: photos 2..5 show items 3..5
    items, files = list(range(6)), list(range(5))
    table = {}
    for photo in range(5):
        table[(photo if photo < 2 else photo + 1, photo)] = 400.0
    assign = align_photos(items, files, _score_map(table))
    assert assign == {0: 0, 1: 1, 3: 2, 4: 3, 5: 4}
    assert 2 not in assign


def test_duplicate_photo_is_skipped_once():
    # six photos for five items: photos 2 and 3 show the same item
    items, files = list(range(5)), list(range(6))
    table = {(0, 0): 400.0, (1, 1): 400.0, (2, 2): 400.0, (2, 3): 400.0, (3, 4): 400.0, (4, 5): 400.0}
    assign = align_photos(items, files, _score_map(table))
    assert sorted(assign) == [0, 1, 2, 3, 4]
    assert len(set(assign.values())) == 5
