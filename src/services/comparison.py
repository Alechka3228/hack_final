import json
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "result.csv"
OUTPUT_FILE = DATA_DIR / "comparison.csv"

COLUMNS = [
    "APP_ID",
    "PREFIX",
    "CLASS",
    "SUFFIX",
    "ARRAY_KEY",
    "KEY",
    "PATH",
    "VALUE_BEFORE",
    "VALUE_AFTER",
    "ADJUSTED_BEFORE",
    "ADJUSTED_AFTER",
    "DIFF_FLAG",
    "CHANGE_TYPE"
]

# Ключ идентификации атрибута. Элементы массивов опознаются по ARRAY_KEY,
# а не по позиции, поэтому порядок строк в срезах не влияет на результат.
ID_FIELDS = ("APP_ID", "PREFIX", "CLASS", "SUFFIX", "ARRAY_KEY", "KEY")


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def write_csv(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def build_path(row):
    # PATH = PREFIX.CLASS.SUFFIX.KEY без пустых частей (ARRAY_KEY в путь не входит)
    parts = [row["PREFIX"], row["CLASS"], row["SUFFIX"], row["KEY"]]
    return ".".join(p for p in parts if p)


def comparison(data):
    """
    data: список строк union (dict) с колонками
          APP_ID, SOURCE, PREFIX, CLASS, SUFFIX, ARRAY_KEY, KEY, VALUE, ADJUSTED_VALUE
    Возвращает список строк (dict) с колонками COLUMNS:
    по одной строке на каждый уникальный атрибут заявки.
    """
    before, after = {}, {}
    order = []  # порядок первого появления: сначала AFTER, затем только-BEFORE

    def ident(row):
        return tuple(row[f] for f in ID_FIELDS)

    after_rows = [r for r in data if r["SOURCE"] == "AFTER"]
    before_rows = [r for r in data if r["SOURCE"] == "BEFORE"]

    for r in after_rows:
        k = ident(r)
        after[k] = r
        if k not in order:
            order.append(k)
    for r in before_rows:
        k = ident(r)
        before[k] = r
        if k not in order:
            order.append(k)

    result = []
    for k in order:
        b, a = before.get(k), after.get(k)
        base = b or a

        value_before = b["VALUE"] if b else ""
        value_after = a["VALUE"] if a else ""
        adj_before = b["ADJUSTED_VALUE"] if b else ""
        adj_after = a["ADJUSTED_VALUE"] if a else ""

        if b is None:
            change_type = "ATTRIBUTE_NEW"
        elif a is None:
            change_type = "ATTRIBUTE_REMOVED"
        elif value_before != value_after:
            # сравниваем фактические значения, а не бакеты
            change_type = "VALUE_CHANGED"
        else:
            change_type = "SAME"

        result.append({
            "APP_ID": base["APP_ID"],
            "PREFIX": base["PREFIX"],
            "CLASS": base["CLASS"],
            "SUFFIX": base["SUFFIX"],
            "ARRAY_KEY": base["ARRAY_KEY"],
            "KEY": base["KEY"],
            "PATH": build_path(base),
            "VALUE_BEFORE": value_before,
            "VALUE_AFTER": value_after,
            "ADJUSTED_BEFORE": adj_before,
            "ADJUSTED_AFTER": adj_after,
            "DIFF_FLAG": 0 if change_type == "SAME" else 1,
            "CHANGE_TYPE": change_type,
        })
    return result


if __name__ == "__main__":
    rows = read_csv(INPUT_FILE)
    write_csv(OUTPUT_FILE, comparison(rows))