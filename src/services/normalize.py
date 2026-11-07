import json
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

INPUT_DIRS = [
    DATA_DIR / "BEFORE",
    DATA_DIR / "AFTER",
]
OUTPUT_FILE = DATA_DIR / "result.csv"

ARRAY_SUFFIX = {
    "scoreCardResult": "scoreCard",
    "rejectReasons": "reason",
}


OBJECT_SUFFIX = {
    "limitResult": "Limit",
}


BUCKETS = {
    "company.scoreCardResult.value": [
        (0, 0.3, "(0 - 0.3]"),
        (0.3, 0.6, "(0.3 - 0.6]"),
        (0.6, 1, "(0.6 - 1]"),
    ],
}

COLUMNS = [
    "APP_ID",
    "SOURCE",
    "PREFIX",
    "CLASS",
    "SUFFIX",
    "ARRAY_KEY",
    "KEY",
    "VALUE",
    "ADJUSTED_VALUE",
]


def find_app_id(data):
    preferred_keys = {"application_id", "app_id", "appid", "APP_ID"}

    def search(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key.lower() in preferred_keys and not isinstance(value, (dict, list)):
                    return value

            for value in node.values():
                result = search(value)
                if result is not None:
                    return result

        elif isinstance(node, list):
            for value in node:
                result = search(value)
                if result is not None:
                    return result

        return None

    result = search(data)
    return "" if result is None else result


def scalar_to_string(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def adjusted_value(full_path, value):
    """Применяет интервальную замену, если для пути настроены интервалы."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        for lower, upper, label in BUCKETS.get(full_path, []):
            if lower < value <= upper:
                return label
    return scalar_to_string(value)


def array_item_key(item, index):
    """Для объекта массива выбирает удобное значение для ARRAY_KEY."""
    if isinstance(item, dict):
        for key in ("name", "product_name", "modelName", "code", "id"):
            if key in item and not isinstance(item[key], (dict, list)):
                return scalar_to_string(item[key])
    return str(index)


def convert_json(data, source):
    app_id = find_app_id(data)
    rows = []

    def add_row(path, value, array_context=None, scalar_array=False):
        if not path:
            return

        prefix = path[0]
        full_path = ".".join(path)

        if array_context:
            class_name, suffix, array_key, base_length = array_context
            key = ".".join(path[base_length:]) or "value"
        else:
            class_name = path[1] if len(path) > 1 else ""
            suffix = OBJECT_SUFFIX.get(class_name, "")
            key = ".".join(path[2:]) if len(path) > 2 else path[-1]
            array_key = ""

        if scalar_array:
            key = "code"

        rows.append({
            "APP_ID": scalar_to_string(app_id),
            "SOURCE": source.name,
            "PREFIX": prefix,
            "CLASS": class_name,
            "SUFFIX": suffix,
            "ARRAY_KEY": array_key,
            "KEY": key,
            "VALUE": scalar_to_string(value),
            "ADJUSTED_VALUE": adjusted_value(full_path, value),
        })

    def walk(node, path=None, array_context=None):
        path = path or []

        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, path + [str(key)], array_context)

        elif isinstance(node, list):
            array_name = path[-1] if path else ""
            suffix = ARRAY_SUFFIX.get(array_name, array_name)

            for index, item in enumerate(node):
                if isinstance(item, (dict, list)):
                    context = (
                        array_name,
                        suffix,
                        array_item_key(item, index),
                        len(path),
                    )
                    walk(item, path, context)
                else:
                    # Например, rejectReasons: ["AGELOW@21", "NOINCOME"]
                    item_value = scalar_to_string(item)
                    rows.append({
                        "APP_ID": scalar_to_string(app_id),
                        "SOURCE": source,
                        "PREFIX": path[0] if path else "",
                        "CLASS": array_name,
                        "SUFFIX": suffix,
                        "ARRAY_KEY": item_value,
                        "KEY": "code",
                        "VALUE": item_value,
                        "ADJUSTED_VALUE": item_value,
                    })

        else:
            add_row(path, node, array_context)

    walk(data)
    return rows


all_rows = []

for folder_name in INPUT_DIRS:
    folder = Path(folder_name)

    if not folder.exists():
        print(f"Папка не найдена, пропускаю: {folder}")
        continue

    for json_file in folder.rglob("*.json"):
        try:
            with json_file.open("r", encoding="utf-8-sig") as file:
                data = json.load(file)

            all_rows.extend(convert_json(data, folder_name))

        except (json.JSONDecodeError, OSError) as error:
            print(f"Не удалось обработать {json_file}: {error}")

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=COLUMNS,
        delimiter=";",
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(all_rows)

print(f"Готово: {OUTPUT_FILE}, строк: {len(all_rows)}")
