"""Exo 2 - ABCD Records (Level 1 + 2 + 3)."""
from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum

_ids = itertools.count(1)


def _next_id(prefix: str) -> str:
    return f"{prefix}-{next(_ids):04d}"


# ---------------------------------------------------------------- items

class Item(ABC):
    def __init__(self, code: str, title: str, artist: str, price: float,
                 stock: int = 0) -> None:
        self.code = code
        self.title = title
        self.artist = artist
        self.price = price
        self.stock = stock

    def is_available(self, quantity: int = 1) -> bool:
        return self.stock >= quantity

    def remove_stock(self, quantity: int) -> None:
        if not self.is_available(quantity):
            raise ValueError(f"not enough stock for {self.code}")
        self.stock -= quantity

    @property
    @abstractmethod
    def media(self) -> str: ...

    def __repr__(self) -> str:
        return f"{self.media}({self.code}, {self.title!r})"


class CD(Item):
    def __init__(self, code, title, artist, price, stock=0, tracks: int = 12):
        super().__init__(code, title, artist, price, stock)
        self.tracks = tracks

    @property
    def media(self) -> str:
        return "CD"


class Tape(Item):
    def __init__(self, code, title, artist, price, stock=0, length_min: int = 60):
        super().__init__(code, title, artist, price, stock)
        self.length_min = length_min

    @property
    def media(self) -> str:
        return "Tape"


# ---------------------------------------------------------------- people

class Member(ABC):
    def __init__(self, name: str, address: str) -> None:
        self.member_id = _next_id("MEM")
        self.name = name
        self.address = address
        self.orders: list[Order] = []

    discount_rate = 0.0
    has_priority = False
    can_order_unavailable = False

    def place_order(self, lines: list[tuple[Item, int]]) -> Order:
        order = Order(self)
        for item, qty in lines:
            order.add_line(item, qty)
        self.orders.append(order)
        return order

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.member_id}, {self.name!r})"


class RegularMember(Member):
    pass


class RoyalMember(Member):
    discount_rate = 0.10
    has_priority = True
    can_order_unavailable = True


class NonMember:
    def __init__(self, name: str, address: str) -> None:
        self.name = name
        self.address = address
        self.application: MembershipApplication | None = None

    def receive_application(self, form: MembershipApplication) -> None:
        self.application = form


@dataclass
class MembershipApplication:
    applicant_name: str
    address: str
    sent_on: date = field(default_factory=date.today)
    id: str = field(default_factory=lambda: _next_id("APP"))


# ---------------------------------------------------------------- orders

class OrderStatus(Enum):
    RECEIVED = "received"
    PROCESSED = "processed"
    PAID = "paid"
    REJECTED = "rejected"


@dataclass
class OrderLine:
    item: Item
    quantity: int
    unit_price: float
    backordered: bool = False

    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity


class Order:
    def __init__(self, member: Member) -> None:
        self.id = _next_id("ORD")
        self.member = member
        self.date = date.today()
        self.lines: list[OrderLine] = []  # composition
        self.status = OrderStatus.RECEIVED

    def add_line(self, item: Item, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be > 0")
        self.lines.append(OrderLine(item, quantity, item.price))

    def shippable_lines(self) -> list[OrderLine]:
        return [l for l in self.lines if not l.backordered]

    def total(self) -> float:
        gross = sum(l.subtotal for l in self.shippable_lines())
        return round(gross * (1 - self.member.discount_rate), 2)


@dataclass
class Invoice:
    order: Order
    amount: float
    issued_on: date = field(default_factory=date.today)
    id: str = field(default_factory=lambda: _next_id("INV"))
    payment: Payment | None = None

    def print(self) -> str:
        rows = [f"INVOICE {self.id} - order {self.order.id} - {self.order.member.name}"]
        for l in self.order.shippable_lines():
            rows.append(f"  {l.item.title:<22} x{l.quantity} {l.subtotal:>7.2f}")
        if self.order.member.discount_rate:
            rows.append(f"  discount {self.order.member.discount_rate:.0%}")
        rows.append(f"  TOTAL {self.amount:.2f}")
        return "\n".join(rows)


@dataclass
class ShippingList:
    order: Order
    id: str = field(default_factory=lambda: _next_id("SHP"))

    def print(self) -> str:
        rows = [f"SHIPPING {self.id} -> {self.order.member.address}"
                + ("  [PRIORITY]" if self.order.member.has_priority else "")]
        rows += [f"  {l.item!r} x{l.quantity}" for l in self.order.shippable_lines()]
        return "\n".join(rows)


class DailyRecordsFile:
    def __init__(self) -> None:
        self.records: dict[date, list[Order]] = {}

    def save(self, order: Order) -> None:
        self.records.setdefault(order.date, []).append(order)

    def orders_of(self, day: date) -> list[Order]:
        return self.records.get(day, [])


# ---------------------------------------------------------------- payment

class Payment(ABC):
    def __init__(self, amount: float) -> None:
        self.id = _next_id("PAY")
        self.amount = amount
        self.paid_on: date | None = None

    @abstractmethod
    def validate(self) -> bool: ...

    def pay(self) -> None:
        if not self.validate():
            raise ValueError(f"{type(self).__name__} rejected")
        self.paid_on = date.today()


class Cash(Payment):
    def validate(self) -> bool:
        return self.amount > 0


class Check(Payment):
    def __init__(self, amount: float, check_number: str, bank: str) -> None:
        super().__init__(amount)
        self.check_number = check_number
        self.bank = bank

    def validate(self) -> bool:
        return self.amount > 0 and self.check_number.isdigit()


class BankDraft(Payment):
    def __init__(self, amount: float, draft_number: str, issuing_bank: str) -> None:
        super().__init__(amount)
        self.draft_number = draft_number
        self.issuing_bank = issuing_bank

    def validate(self) -> bool:
        return self.amount > 0 and bool(self.draft_number)


# ---------------------------------------------------------------- clerks

class OrderProcessingClerk:
    def __init__(self, name: str, members: dict[str, Member],
                 records: DailyRecordsFile) -> None:
        self.name = name
        self.members = members
        self.records = records
        self.reorders: list[OrderLine] = []

    def verify_membership(self, customer) -> bool:
        return isinstance(customer, Member) and customer.member_id in self.members

    def send_application(self, person: NonMember) -> MembershipApplication:
        form = MembershipApplication(person.name, person.address)
        person.receive_application(form)
        return form

    def check_availability(self, order: Order) -> None:
        for line in order.lines:
            if line.item.is_available(line.quantity):
                continue
            if not order.member.can_order_unavailable:
                order.status = OrderStatus.REJECTED
                raise ValueError(f"{line.item.title} unavailable")
            line.backordered = True  # Royal only: reorder from supplier
            self.reorders.append(line)

    def process_order(self, order: Order) -> tuple[Invoice, ShippingList]:
        if not self.verify_membership(order.member):
            order.status = OrderStatus.REJECTED
            raise PermissionError("only members can order")
        self.check_availability(order)
        for line in order.shippable_lines():
            line.item.remove_stock(line.quantity)
        order.status = OrderStatus.PROCESSED
        self.records.save(order)
        return Invoice(order, order.total()), ShippingList(order)


class CollectionDepartmentClerk:
    def __init__(self, name: str) -> None:
        self.name = name

    def collect(self, invoice: Invoice, payment: Payment) -> None:
        if invoice.payment is not None:
            raise ValueError("invoice already paid")
        if payment.amount != invoice.amount:
            raise ValueError(f"expected {invoice.amount}, got {payment.amount}")
        payment.pay()
        invoice.payment = payment
        invoice.order.status = OrderStatus.PAID


# ---------------------------------------------------------------- demo

def main() -> None:
    records = DailyRecordsFile()
    royal = RoyalMember("Rita", "12 rue de la Paix, Paris")
    members = {royal.member_id: royal}
    clerk = OrderProcessingClerk("Oscar", members, records)
    cashier = CollectionDepartmentClerk("Clara")

    # non-member gets an application form
    bob = NonMember("Bob", "3 av. Foch")
    print("application sent:", clerk.send_application(bob).id)

    # scenario: Royal member orders 2 CDs, one unavailable, pays by check
    thriller = CD("CD01", "Thriller", "M. Jackson", 12.0, stock=5)
    rare = CD("CD02", "Rare Live 1971", "Unknown", 20.0, stock=0)
    order = royal.place_order([(thriller, 1), (rare, 1)])
    invoice, shipping = clerk.process_order(order)
    print(invoice.print())
    print(shipping.print())
    print("reordered:", [l.item.title for l in clerk.reorders])

    cashier.collect(invoice, Check(invoice.amount, "0012345", "BNP"))
    print("order status:", order.status.value,
          "| records today:", len(records.orders_of(date.today())))


if __name__ == "__main__":
    main()
