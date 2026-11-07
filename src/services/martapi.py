from dataclasses import dataclass
from typing import Iterable
import pandas as pd


@dataclass
class Mart:
    storage: pd.DataFrame

    def _to_mask(self, **filters):
        mask = pd.Series(True, index=self.storage.index)
        if "path" in filters:
            if isinstance(filters["path"], str):
                mask &= self.storage["PATH"] == filters["path"]
            elif isinstance(filters["path"], list):
                mask &= self.storage["PATH"] in filters["path"]

        if "path_prefix" in filters:
            mask &= self.storage["PATH"].str.startswith(filters["path_prefix"])

        if "key" in filters:
            mask &= self.storage["KEY"] == filters["key"]

        if "array_key" in filters:
            mask &= self.storage["ARRAY_KEY"] == filters["key"]

        if "diff_flag" in filters:
            mask &= self.storage["DIFF_FLAG"] == filters["diff_flag"]

        if "change_type" in filters:
            if isinstance(filters["change_type"], str):
                mask &= self.storage["CHANGE_TYPE"] == filters["change_type"]
            if isinstance(filters["change_type"], list):
                mask &= self.storage["CHANGE_TYPE"] in filters["change_type"]

        if "value_before" in filters:
            mask &= self.storage["VALUE_BEFORE"] == filters["value_before"]

        if "value_after" in filters:
            mask &= self.storage["VALUE_AFTER"] == filters["value_after"]

        if "app_ids" in filters:
            mask &= self.storage["APP_ID"] in filters["app_ids"]

        return mask

    def _filtered(self, **filters) -> pd.DataFrame:
        if filters:
            return self.storage[self._to_mask(**filters)]
        return self.storage

    def row(self, **filters) -> Iterable[dict]:
        df = self._filtered(**filters)
        return [dict(df.iloc[i]) for i in range(len(df))]

    def count(self, **filters) -> int:
        df = self._filtered(**filters)
        return len(df)

    def app_ids(self, **filters) -> list[str]:
        df = self._filtered(**filters)
        return sorted(list(df["APP_ID"].unique()))

    def segments(self) -> Iterable[dict]:
        return self.storage[
            [
                "APP_ID",
                "DECISION_BEFORE",
                "DECISION_AFTER",
                "DECISION_CHANGED",
                "PRODUCTS",
                "TOP_OFFER_BEFORE",
                "TOP_OFFER_AFTER",
                "PARTNER_TYPE",
                "ROUTING_METHOD",
                "PD_MODEL_BEFORE",
                "PD_MODEL_AFTER",
                "CUTOFF_BEFORE",
                "CUTOFF_AFTER",
                "REJECT_REASON_BEFORE",
                "REJECT_REASON_AFTER",
                "SCORE_OKB_BEFORE",
                "SCORE_OKB_AFTER",
            ]
        ]

    def total_apps(self) -> int:
        return len(self.storage["APP_ID"].unique())
