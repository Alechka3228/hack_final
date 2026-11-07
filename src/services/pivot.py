import pandas as pd
from io import StringIO


def read_csv(sep: str, csv: str) -> pd.DataFrame:
    return pd.read_csv(StringIO(csv), sep=sep)


def pivot_table(
    index: str | list[str],
    values: str | list[str],
    aggfunc: str | list[str],
    df: pd.DataFrame,
) -> pd.DataFrame:
    return pd.pivot_table(df, index=index, values=values, aggfunc=aggfunc)


def export_html(df: pd.DataFrame) -> str:
    return df.to_html()


def export_csv(df: pd.DataFrame) -> str:
    return df.to_csv()
