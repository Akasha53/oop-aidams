"""Creational - Factory Method: refactor of process_payment()."""
from __future__ import annotations

from abc import ABC, abstractmethod


class PaymentProcessor(ABC):
    """Contract that every payment method follows."""

    method = ""  # key used by the factory, echoed in the result
    error = ""   # message returned when validate() fails

    @abstractmethod
    def validate(self, details: dict) -> bool:
        """True if the details can be used for this payment method."""

    @abstractmethod
    def process(self, amount: float, details: dict) -> dict:
        """Charge the amount and return a result dict."""

    def _success(self, amount: float, fee: float) -> dict:
        return {"success": True, "method": self.method,
                "amount": round(amount + fee, 2), "fee": round(fee, 2)}

    def _failure(self) -> dict:
        return {"success": False, "error": self.error}


class CreditCardProcessor(PaymentProcessor):
    method = "credit_card"
    error = "Invalid card number or CVV"
    RATE = 0.029

    def validate(self, details: dict) -> bool:
        card = details.get("card_number") or ""
        cvv = details.get("cvv") or ""
        return len(card) == 16 and card.isdigit() and len(cvv) == 3 and cvv.isdigit()

    def process(self, amount: float, details: dict) -> dict:
        if not self.validate(details):
            return self._failure()
        return self._success(amount, amount * self.RATE)


class BankTransferProcessor(PaymentProcessor):
    method = "bank_transfer"
    error = "Invalid IBAN"
    FLAT_FEE = 1.50

    def validate(self, details: dict) -> bool:
        return len(details.get("iban") or "") >= 15

    def process(self, amount: float, details: dict) -> dict:
        if not self.validate(details):
            return self._failure()
        return self._success(amount, self.FLAT_FEE)


class PayPalProcessor(PaymentProcessor):
    method = "paypal"
    error = "Invalid PayPal email"

    def validate(self, details: dict) -> bool:
        return "@" in (details.get("email") or "")

    def process(self, amount: float, details: dict) -> dict:
        if not self.validate(details):
            return self._failure()
        return self._success(amount, amount * 0.034 + 0.30)


class PaymentFactory:
    """Turns a payment type ("paypal") into a processor, with a dict instead of if/elif."""

    _processors: dict[str, type[PaymentProcessor]] = {
        "credit_card": CreditCardProcessor,
        "bank_transfer": BankTransferProcessor,
        "paypal": PayPalProcessor,
    }

    @classmethod
    def register(cls, payment_type: str, processor_cls: type[PaymentProcessor]) -> None:
        """Add a payment method without touching the classes above."""
        cls._processors[payment_type] = processor_cls

    def get_processor(self, payment_type: str) -> PaymentProcessor:
        try:
            return self._processors[payment_type]()
        except KeyError:
            raise ValueError(f"Unknown payment type: {payment_type}") from None


# New business need: crypto. One new class and one register() call, nothing else changes.
class CryptoProcessor(PaymentProcessor):
    method = "crypto"
    error = "Invalid wallet address"
    RATE = 0.01

    def validate(self, details: dict) -> bool:
        wallet = details.get("wallet") or ""
        return wallet.startswith("0x") and len(wallet) == 42

    def process(self, amount: float, details: dict) -> dict:
        if not self.validate(details):
            return self._failure()
        return self._success(amount, amount * self.RATE)


PaymentFactory.register("crypto", CryptoProcessor)


if __name__ == "__main__":
    factory = PaymentFactory()
    print(factory.get_processor("credit_card").process(
        100.0, {"card_number": "1234567890123456", "cvv": "123"}))
    print(factory.get_processor("bank_transfer").process(
        100.0, {"iban": "FR7630006000011234567890189", "bic": "BNPAFRPP"}))
    print(factory.get_processor("paypal").process(100.0, {"email": "client@shop.com"}))
    print(factory.get_processor("crypto").process(100.0, {"wallet": "0x" + "a" * 40}))
