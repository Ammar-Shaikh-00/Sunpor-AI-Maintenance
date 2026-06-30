"""Group aggregator.

Collapses a per-signal FeatureVector into per-signal_group aggregate features
that the rule engine evaluates. Group membership comes from the catalog, so no
signal names or ids are hardcoded.
"""

from __future__ import annotations

import numpy as np

from features.models import FeatureVector

# (aggregate suffix, SignalFeatures attribute) pairs.
_NUMERIC_AGGS = (
    ("mean_of_means", "mean"),
    ("mean_of_lasts", "last_val"),
    ("mean_of_trends", "trend"),
    ("mean_of_stds", "std"),
    ("mean_of_rocs", "roc"),
)


class GroupAggregator:
    """Aggregates per-signal features into per-group features."""

    def __init__(self, catalog: list[dict]) -> None:
        self._group_of = {
            s["id"]: s.get("signal_group", "")
            for s in catalog
            if s.get("id") is not None
        }

    def aggregate(self, vector: FeatureVector) -> dict[str, float]:
        """Return {group}__{agg} features for every group present in vector."""
        # group -> {attr: [values]} plus bad-quality bookkeeping.
        buckets: dict[str, dict] = {}

        for signal_id, sf in vector.signal_features.items():
            group = self._group_of.get(signal_id, sf.signal_group)
            if not group:
                continue
            bucket = buckets.setdefault(
                group,
                {attr: [] for _, attr in _NUMERIC_AGGS} | {"_n": 0, "_bad": 0},
            )
            bucket["_n"] += 1
            if sf.has_bad_quality:
                bucket["_bad"] += 1
            for _, attr in _NUMERIC_AGGS:
                value = getattr(sf, attr)
                if value is not None:
                    bucket[attr].append(float(value))

        features: dict[str, float] = {}
        for group, bucket in buckets.items():
            for suffix, attr in _NUMERIC_AGGS:
                values = bucket[attr]
                if values:
                    features[f"{group}__{suffix}"] = float(np.mean(values))
            n = bucket["_n"]
            features[f"{group}__bad_quality_ratio"] = (
                bucket["_bad"] / n if n else 0.0
            )
        return features
