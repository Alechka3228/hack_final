from matplotlib import pyplot as plt
from io import BytesIO
import seaborn as sns
import pandas as pd


def barplot_agg(aggfunc: str, column: str, df: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    grouped = df.groupby(column)[column].agg(aggfunc)
    sns.barplot(grouped)
    plt.title(f"{aggfunc} в зависимости от {column}")
    plt.xlabel(column)
    plt.ylabel(aggfunc)
    plt.savefig(buffer)
    return buffer
