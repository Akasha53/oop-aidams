"""Behavioral - Template Method: the ETL workflow is written once, in the base class."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod


class DataPipeline(ABC):
    name = ""                               # "CSV", "API"... used in the logs
    required_fields: tuple[str, ...] = ()   # checked by validate()

    def __init__(self, source: str) -> None:
        self.source = source
        self.data: list[dict] | None = None
        self.loaded: list[dict] = []        # stands for the destination database
        self.logs: list[str] = []

    def run(self) -> str:
        """Template method: the order of the steps is fixed here and nowhere else."""
        try:
            self.connect()
            self.data = self.extract()
            self.logs.append(f"Extracted {len(self.data)} records")
            self.data = [self.transform(record) for record in self.data]
            self.validate()
            self.before_load()
            self.load()
        finally:
            self.cleanup()  # runs even when validation fails
        return f"{self.name} Pipeline finished"

    # --- steps each pipeline must write
    @abstractmethod
    def extract(self) -> list[dict]: ...

    @abstractmethod
    def transform(self, record: dict) -> dict: ...

    # --- common steps, written once
    def validate(self) -> None:
        for record in self.data:
            if any(field not in record for field in self.required_fields):
                raise ValueError(f"Invalid record structure: {record}")
        self.logs.append("Validation passed")

    def load(self) -> None:
        self.loaded.extend(self.data)
        self.logs.append(f"Loaded {len(self.data)} records successfully")

    def cleanup(self) -> None:
        self.data = None
        self.logs.append("Cleanup complete")

    # --- hooks: a default behaviour that a subclass may override
    def connect(self) -> None:
        self.logs.append(f"Connecting to {self.name} source: {self.source}")

    def before_load(self) -> None:
        pass


class CSVPipeline(DataPipeline):
    name = "CSV"
    required_fields = ("id", "name")

    def extract(self) -> list[dict]:
        return [{"id": 1, "name": "Alice", "age": "30"}, {"id": 2, "name": "Bob", "age": "25"}]

    def transform(self, record: dict) -> dict:
        return {**record, "age": int(record["age"]), "name": record["name"].upper()}


class APIPipeline(DataPipeline):
    name = "API"
    required_fields = ("user_id", "username")

    def extract(self) -> list[dict]:
        return [{"user_id": 101, "username": "Charlie", "score": "85"},
                {"user_id": 102, "username": "Diana", "score": "92"}]

    def transform(self, record: dict) -> dict:
        score = int(record["score"])
        return {**record, "score": score, "username": record["username"].lower(),
                "grade": "A" if score >= 90 else "B"}

    def before_load(self) -> None:  # hook: the API table is stored best score first
        self.data.sort(key=lambda r: r["score"], reverse=True)


class DatabasePipeline(DataPipeline):
    name = "Database"
    required_fields = ("product_id", "price")

    def extract(self) -> list[dict]:
        return [{"product_id": 501, "product_name": "laptop", "price": 1200},
                {"product_id": 502, "product_name": "mouse", "price": 25}]

    def transform(self, record: dict) -> dict:
        price = float(record["price"])
        return {**record, "price": price, "product_name": record["product_name"].title(),
                "tax": price * 0.2}


# Check of the exercise: a new pipeline only writes what is specific to it
class XMLPipeline(DataPipeline):
    name = "XML"
    required_fields = ("order_id", "total")
    SAMPLE = '<orders><order id="9001" customer="eve" total="59.90"/>' \
             '<order id="9002" customer="frank" total="120"/></orders>'

    def extract(self) -> list[dict]:
        return [dict(order.attrib) for order in ET.fromstring(self.SAMPLE)]

    def transform(self, record: dict) -> dict:
        return {"order_id": int(record["id"]), "customer": record["customer"].title(),
                "total": float(record["total"])}


if __name__ == "__main__":
    for pipeline in (CSVPipeline("data/users.csv"), APIPipeline("https://api.example.com/users"),
                     DatabasePipeline("postgresql://localhost/mydb"), XMLPipeline("data/orders.xml")):
        result = pipeline.run()
        print("\n".join(pipeline.logs))
        print(result, end="\n\n")
