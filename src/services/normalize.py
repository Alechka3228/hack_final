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

DEFAULTS = {
    "exclude": [
        "appData.request_id",
        "appData.createDateTime",
        "company.decisionResult.calculatedAt",
    ],
    "arrays": {
        "decisionResult.available_offers": ["product_id", "type"],
        "decisionResult.product_trials": ["product_id"],
        "decisionResult.product_trials.rules": ["name"],
        "decisionResult.product_trials.scoring.scoreModels": ["modelName"],
        "decisionResult.scoring": ["modelName"],
        "decisionResult.scoring.value": "index",
        "ext_data": ["body.action"],
        "product_catalog": ["mfo_id", "product_id"],
        "tariff_matrix": ["mfo_id", "product_id"],
        "company.scoreCardResult": ["name"],
        "company.rejectReasons": "value",
    },
    "buckets": [0, 0.3, 0.6, 1, 500, 700, 900, 10000, 100000, 250000],
    "layout": {
        "company.scoreCardResult": "scoreCard",
        "company.limitResult": "Limit",
        "company.rejectReasons": "reason",
    },
    "buckets_by_path": {
        "company.scoreCardResult.value": {
            "bounds": [0, 0.3, 0.6, 1],
            "labels": ["(-∞ - 0]", "(0 - 0.3]", "(0.3 - 0.6]", "(0.6 - 1]", "(1 - +∞)"],
        },
        "company.limitResult.limit": {
            "bounds": [0, 100000, 250000],
            "labels": ["(-∞ - 0]", "(0 - 100K]", "(100K - 250K]", "(250K - +∞)"],
        },
    },
}

IGNORE_CLASSES = [
    "request_id",
    "createDateTime",
    "application_id"
  ]

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

def get_by_path(data, path):
    """Получает значение по пути вроде body.action."""
    value = data
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def format_bound(value):
    if isinstance(value, float) and value.is_integer():
        value = int(value)

    if isinstance(value, (int, float)) and abs(value) >= 1000:
        number = value / 1000
        number = int(number) if number.is_integer() else number
        return f"{number}K"

    return str(value)


def bucket_label(value, bounds, labels=None):
    """Интервалы: (-∞, первый], (первый, второй] ... (последний, +∞)."""
    if value <= bounds[0]:
        index = 0
    else:
        index = len(bounds)
        for i, bound in enumerate(bounds[1:], start=1):
            if value <= bound:
                index = i
                break

    if labels:
        return labels[index]

    if index == 0:
        return f"(-∞ - {format_bound(bounds[0])}]"
    if index == len(bounds):
        return f"({format_bound(bounds[-1])} - +∞)"

    return f"({format_bound(bounds[index - 1])} - {format_bound(bounds[index])}]"


def adjusted_value(full_path, value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return scalar_to_string(value)

    path_config = DEFAULTS.get("buckets_by_path", {}).get(full_path)

    if path_config:
        return bucket_label(
            value,
            path_config["bounds"],
            path_config.get("labels"),
        )

    bounds = DEFAULTS.get("buckets", [])
    if bounds:
        return bucket_label(value, bounds)

    return scalar_to_string(value)


def array_item_key(array_path, item, index):
    selectors = DEFAULTS.get("arrays", {}).get(array_path)

    if selectors == "index":
        return str(index)

    if selectors == "value":
        return scalar_to_string(item)

    if isinstance(selectors, list):
        parts = []
        for selector in selectors:
            value = get_by_path(item, selector)
            if value is not None:
                parts.append(scalar_to_string(value))
        if parts:
            return "|".join(parts)

    # Запасной вариант, если путь массива отсутствует в настройках.
    if isinstance(item, dict):
        for key in ("name", "product_name", "modelName", "code", "id"):
            if key in item and not isinstance(item[key], (dict, list)):
                return scalar_to_string(item[key])

    return str(index)

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

def convert_json(data, source):
    app_id = find_app_id(data)
    rows = []

    def add_row(path, value, array_context=None, scalar_array=False):
        if not path:
            return

        full_path = ".".join(path)

        if full_path in DEFAULTS.get("exclude", []):
            return

        prefix = path[0]

        if array_context:
            class_name, suffix, array_key, base_length = array_context
            key = ".".join(path[base_length:]) or "value"
        else:
            class_name = path[1] if len(path) > 1 else ""
            layout_path = ".".join(path[:2])
            suffix = DEFAULTS.get("layout", {}).get(layout_path, "")
            key = ".".join(path[2:]) if len(path) > 2 else path[-1]
            array_key = ""

        if class_name in IGNORE_CLASSES:
            return

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

        if ".".join(path) in DEFAULTS.get("exclude", []):
            return

        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, path + [str(key)], array_context)

        elif isinstance(node, list):
            array_path = ".".join(path)
            array_name = path[-1] if path else ""
            suffix = DEFAULTS.get("layout", {}).get(array_path, array_name)

            for index, item in enumerate(node):
                if isinstance(item, (dict, list)):
                    context = (
                        array_name,
                        suffix,
                        array_item_key(array_path, item, index),
                        len(path),
                    )
                    walk(item, path, context)
                else:
                    item_value = scalar_to_string(item)
                    full_path = array_path

                    rows.append({
                        "APP_ID": scalar_to_string(app_id),
                        "SOURCE": source.name,
                        "PREFIX": path[0] if path else "",
                        "CLASS": array_name,
                        "SUFFIX": suffix,
                        "ARRAY_KEY": item_value,
                        "KEY": "code",
                        "VALUE": item_value,
                        "ADJUSTED_VALUE": adjusted_value(full_path, item),
                    })

        else:
            add_row(path, node, array_context)

    walk(data)
    return rows

def normalize_json_files():
    all_rows = []
    
    for folder_name in INPUT_DIRS:
        folder = Path(folder_name)

        if not folder.exists():
            Exception(f"Папка не найдена: {folder}")
            continue

        for json_file in folder.rglob("*.json"):
            try:
                with json_file.open("r", encoding="utf-8-sig") as file:
                    data = json.load(file)

                all_rows.extend(convert_json(data, folder_name))

            except (json.JSONDecodeError, OSError) as error:
                Exception(f"Не удалось обработать {json_file}: {error}")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=COLUMNS,
            delimiter=";",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(all_rows)


if __name__ == "__main__":  
    normalize_json_files()
