"""Structural - Decorator: each order option wraps the order instead of being a boolean flag."""
from __future__ import annotations

from abc import ABC, abstractmethod


class OrderComponent(ABC):
    @abstractmethod
    def get_cost(self) -> float: ...

    @abstractmethod
    def get_description(self) -> str: ...


class BaseOrder(OrderComponent):
    def __init__(self, base_price: float) -> None:
        self.base_price = base_price

    def get_cost(self) -> float:
        return self.base_price

    def get_description(self) -> str:
        return f"Base price: {self.base_price:.2f}€"


class OrderDecorator(OrderComponent):
    """Wraps another component: adds its own amount and one line of description."""

    def __init__(self, order: OrderComponent) -> None:
        self._order = order

    @property
    def base_price(self) -> float:
        return self._order.base_price

    @abstractmethod
    def _amount(self) -> float:
        """What this option adds to the cost (negative for a discount)."""

    @abstractmethod
    def _label(self) -> str: ...

    def get_cost(self) -> float:
        return self._order.get_cost() + self._amount()

    def get_description(self) -> str:
        return f"{self._order.get_description()}\n{self._label()}: {self._amount():+.2f}€"


class ExpressShippingDecorator(OrderDecorator):
    def _amount(self) -> float:
        return 15.00

    def _label(self) -> str:
        return "Express shipping"


class InsuranceDecorator(OrderDecorator):
    def _amount(self) -> float:
        return self.base_price * 0.05  # 5% of the goods, as in the old code

    def _label(self) -> str:
        return "Insurance (5%)"


class GiftWrapDecorator(OrderDecorator):
    def _amount(self) -> float:
        return 5.00

    def _label(self) -> str:
        return "Gift wrap"


class DiscountDecorator(OrderDecorator):
    def __init__(self, order: OrderComponent, percent: float) -> None:
        super().__init__(order)
        self.percent = percent

    def _amount(self) -> float:
        return -self._order.get_cost() * self.percent / 100

    def _label(self) -> str:
        return f"Discount ({self.percent}%)"


class PremiumMemberDecorator(OrderDecorator):
    def _amount(self) -> float:
        return -self._order.get_cost() * 0.10

    def _label(self) -> str:
        return "Premium member (10%)"


if __name__ == "__main__":
    # The wrapping order is the order of the calculation: no more guessing.
    order = BaseOrder(100.00)
    order = ExpressShippingDecorator(order)
    order = InsuranceDecorator(order)
    order = GiftWrapDecorator(order)
    order = DiscountDecorator(order, percent=15)
    order = PremiumMemberDecorator(order)
    print(order.get_description())
    print(f"Total: {order.get_cost():.2f}€")
