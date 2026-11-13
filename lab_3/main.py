
"""
Лабораторная работа № 3 «Regular expressions».
Вариант 16.

Проверяет 10 столбцов CSV-файла регулярными выражениями,
находит строки с ошибками и вычисляет контрольную сумму.
В лабораторной работе № 5 добавлено логирование.
"""

import csv
import datetime
import json
import logging
import re
from pathlib import Path

from checksum import calculate_checksum, serialize_result


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "16.csv"
REPORT_PATH = BASE_DIR / "validation_report.json"
LOG_PATH = BASE_DIR / "application.log"

VARIANT = 16


# Настройка логирования
def setup_logging() -> None:
    """Настраивает запись логов в файл и консоль."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler()
        ],
        force=True
    )


logger = logging.getLogger(__name__)


# По одному регулярному выражению для каждого столбца.
PATTERNS = {
    "telephone": re.compile(r"\+7-\(\d{3}\)-\d{3}-\d{2}-\d{2}"),
    "height": re.compile(r"(?:0|1|2)\.\d{2}"),
    "inn": re.compile(r"\d{12}"),
    "identifier": re.compile(r"\d{2}-\d{2}/\d{2}"),
    "occupation": re.compile(
        r"[A-Za-zА-Яа-яЁё]+(?:[ -][A-Za-zА-Яа-яЁё]+)*"
    ),
    "latitude": re.compile(r"-?\d{1,2}\.\d+"),
    "blood_type": re.compile(r"(?:A|B|AB|O)[+−]"),
    "issn": re.compile(r"\d{4}-\d{4}"),
    "uuid": re.compile(
        r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}"
    ),
    "date": re.compile(r"\d{4}-\d{2}-\d{2}"),
}


def is_valid(field: str, value: str) -> bool:
    """Проверяет формат значения и дополнительные ограничения поля."""
    if not PATTERNS[field].fullmatch(value):
        return False

    if field == "height":
        height = float(value)
        return 0 < height < 3

    if field == "latitude":
        latitude = float(value)
        return -90 <= latitude <= 90

    if field == "date":
        try:
            datetime.date.fromisoformat(value)
        except ValueError:
            return False

    return True


def read_csv() -> tuple[list[str], list[dict[str, str]]]:
    """Читает исходный CSV в кодировке UTF-16 с разделителем ';'."""
    logger.info("Начато чтение CSV-файла: %s", CSV_PATH)

    with CSV_PATH.open("r", encoding="utf-16", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")

        if reader.fieldnames != list(PATTERNS):
            logger.error("Столбцы CSV не совпадают с ожидаемыми")
            raise ValueError(
                "Столбцы CSV не совпадают с ожидаемыми: "
                + ", ".join(reader.fieldnames or [])
            )

        rows = list(reader)

    if len(rows) != 10_000:
        logger.error("Неверное количество строк: %d", len(rows))
        raise ValueError(f"Ожидалось 10000 строк, получено {len(rows)}.")

    logger.info("CSV-файл успешно прочитан. Строк: %d", len(rows))
    logger.info("Количество проверяемых столбцов: %d", len(PATTERNS))

    return list(PATTERNS), rows


def validate_rows(
    headers: list[str], rows: list[dict[str, str]]
) -> tuple[dict[str, list[int]], list[int]]:
    """
    Возвращает ошибки по каждому полю и общий список ошибочных строк.

    Номер строки данных начинается с 0.
    """
    logger.info("Начата проверка данных регулярными выражениями")

    invalid_by_field = {field: [] for field in headers}
    invalid_rows = set()

    for row_number, row in enumerate(rows):
        for field in headers:
            value = row[field]

            if not is_valid(field, value):
                invalid_by_field[field].append(row_number)
                invalid_rows.add(row_number)

    logger.info(
        "Проверка завершена. Найдено ошибочных строк: %d",
        len(invalid_rows)
    )

    return invalid_by_field, sorted(invalid_rows)


def main() -> None:
    """Выполняет проверку и сохраняет результат."""
    setup_logging()

    logger.info("Запуск программы. Вариант: %d", VARIANT)

    headers, rows = read_csv()

    invalid_by_field, invalid_rows = validate_rows(headers, rows)

    checksum = calculate_checksum(invalid_rows)

    logger.info("Контрольная сумма рассчитана: %s", checksum)

    serialize_result(VARIANT, checksum)

    report = {
        "variant": VARIANT,
        "rows_checked": len(rows),
        "columns_checked": len(headers),
        "invalid_count_by_column": {
            field: len(numbers)
            for field, numbers in invalid_by_field.items()
        },
        "unique_invalid_rows_count": len(invalid_rows),
        "invalid_rows_zero_based": invalid_rows,
        "checksum": checksum,
    }

    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )

    logger.info("Подробный отчёт сохранён: %s", REPORT_PATH)
    logger.info("Работа программы успешно завершена")

    print(f"Вариант: {VARIANT}")
    print(f"Проверено строк: {len(rows)}")
    print(f"Проверено столбцов: {len(headers)}")
    print("Невалидных значений по столбцам:")

    for field, numbers in invalid_by_field.items():
        print(f"  {field}: {len(numbers)}")

    print(f"Уникальных строк с ошибками: {len(invalid_rows)}")
    print(f"Контрольная сумма: {checksum}")
    print("Результат сохранён в result.json")
    print(f"Подробный отчёт сохранён в {REPORT_PATH.name}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Произошла ошибка при выполнении программы")
        raise
