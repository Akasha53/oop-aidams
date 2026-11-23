"""Behavioral - Strategy: one class per report format, chosen at runtime."""
from __future__ import annotations

import html
import json
from abc import ABC, abstractmethod
from pathlib import Path


class FormatStrategy(ABC):
    extension = ""

    @abstractmethod
    def format(self, data: list[dict]) -> str: ...


class PDFFormatStrategy(FormatStrategy):
    extension = ".pdf"

    def format(self, data: list[dict]) -> str:
        rows = [f"| {item['name']:20} | {item['value']:10} |" for item in data]
        return "\n".join(["PDF REPORT", "=" * 50, *rows, "=" * 50, "End of PDF Report"])


class ExcelFormatStrategy(FormatStrategy):
    extension = ".xlsx"  # still tab-separated text, like the original code

    def format(self, data: list[dict]) -> str:
        rows = [f"{item['name']}\t{item['value']}" for item in data]
        return "\n".join(["EXCEL REPORT", "-" * 50, "Name\tValue", *rows, "-" * 50]) + "\n"


class CSVFormatStrategy(FormatStrategy):
    extension = ".csv"

    def format(self, data: list[dict]) -> str:
        return "".join(["name,value\n", *(f"{item['name']},{item['value']}\n" for item in data)])


class JSONFormatStrategy(FormatStrategy):
    extension = ".json"

    def format(self, data: list[dict]) -> str:
        return json.dumps(data, indent=2)


class ReportGenerator:
    """The context: holds the data and delegates the formatting to its strategy."""

    def __init__(self, data: list[dict], strategy: FormatStrategy | None = None) -> None:
        self.data = data
        self._strategy = strategy

    def set_strategy(self, strategy: FormatStrategy) -> None:
        self._strategy = strategy

    def generate_report(self) -> str:
        if self._strategy is None:
            raise ValueError("No format chosen: call set_strategy() first")
        return self._strategy.format(self.data)

    def save_report(self, filename: str) -> Path:
        content = self.generate_report()  # raises before touching the disk if no strategy
        path = Path(filename + self._strategy.extension)
        path.write_text(content, encoding="utf-8")
        return path


# Final test of the exercise: HTML added without modifying any class above
class HTMLFormatStrategy(FormatStrategy):
    extension = ".html"

    def format(self, data: list[dict]) -> str:
        rows = "".join(f"<tr><td>{html.escape(str(item['name']))}</td>"
                       f"<td>{html.escape(str(item['value']))}</td></tr>" for item in data)
        return f"<table><tr><th>Name</th><th>Value</th></tr>{rows}</table>"


if __name__ == "__main__":
    data = [
        {"name": "Sales Q1", "value": 15000},
        {"name": "Sales Q2", "value": 18000},
        {"name": "Sales Q3", "value": 22000},
        {"name": "Sales Q4", "value": 25000},
    ]
    generator = ReportGenerator(data)
    for strategy in (PDFFormatStrategy(), CSVFormatStrategy(), JSONFormatStrategy(), HTMLFormatStrategy()):
        generator.set_strategy(strategy)
        print(f"=== {type(strategy).__name__} ===")
        print(generator.generate_report(), end="\n\n")
