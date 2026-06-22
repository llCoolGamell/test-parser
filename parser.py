"""
Точка входа: запускает GUI-приложение.
Для запуска без GUI используйте: python main.py --cli
"""

import sys


def run_cli():
    """Консольный режим без GUI."""
    import pandas as pd
    from parser import YandexParser
    import os

    queries_file = "requests.txt"
    if not os.path.exists(queries_file):
        print(f"Файл {queries_file} не найден.")
        sys.exit(1)

    with open(queries_file, "r", encoding="utf-8") as f:
        queries = [line.strip() for line in f if line.strip()]

    os.makedirs("output", exist_ok=True)

    parser = YandexParser()
    parser.start(headless=False)

    results = []
    try:
        for i, query in enumerate(queries, start=1):
            print(f"[{i}/{len(queries)}] {query}")
            result = parser.check_query(query)
            results.append({
                "Запрос": result["query"],
                "Есть AI-блок": result["has_ai"],
                "Источник в AI-блоке": result["sources"],
                "Примечание": result["note"],
            })
            pd.DataFrame(results).to_excel("output/result.xlsx", index=False)
    finally:
        parser.close()

    print(f"\nГотово! Результаты: output/result.xlsx")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli()
    else:
        from gui import App
        App().run()
