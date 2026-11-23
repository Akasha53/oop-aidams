"""Structural - Adapter: the legacy XML generator behind the JSON interface the dashboard expects."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod


# Legacy reporting system (can't modify - external library)
class LegacyReportGenerator:
    def generate_report(self, data: dict) -> str:
        """Returns XML format - old system"""
        xml = "<report>\n"
        for key, value in data.items():
            xml += f"  <{key}>{value}</{key}>\n"
        xml += "</report>"
        return xml


# New analytics dashboard expects JSON
class AnalyticsDashboard:
    def display(self, json_data: str) -> None:
        data = json.loads(json_data)
        print("=== Analytics Dashboard ===")
        for key, value in data.items():
            print(f"  {key}: {value}")


class ReportGeneratorInterface(ABC):
    """What the rest of the code expects from a report generator."""

    @abstractmethod
    def generate(self, data: dict) -> str:
        """Return the report as a JSON string."""


class LegacyReportAdapter(ReportGeneratorInterface):
    """Wraps LegacyReportGenerator and converts its XML into JSON."""

    def __init__(self, legacy: LegacyReportGenerator) -> None:
        self._legacy = legacy

    def generate(self, data: dict) -> str:
        root = ET.fromstring(self._legacy.generate_report(data))
        return json.dumps({child.tag: _to_number(child.text) for child in root})


def _to_number(text: str | None):
    """XML only holds text: give back 1234 and 121.55 as numbers."""
    for cast in (int, float):
        try:
            return cast(text)
        except (TypeError, ValueError):
            pass
    return text


def show_report(generator: ReportGeneratorInterface, data: dict) -> None:
    # The conversion is no longer repeated here: the adapter does it
    AnalyticsDashboard().display(generator.generate(data))


if __name__ == "__main__":
    report_generator = LegacyReportAdapter(LegacyReportGenerator())
    show_report(report_generator, {"total_sales": 150000, "orders": 1234, "avg_order": 121.55})
    show_report(report_generator, {"total_items": 5000, "low_stock": 45, "out_of_stock": 12})
