"""Exo 1 - Hospital Management System (Task 1 + 2 + 3)."""
from __future__ import annotations

import hashlib
import itertools
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum

_ids = itertools.count(1)


def _next_id(prefix: str) -> str:
    return f"{prefix}-{next(_ids):04d}"


# ---------------------------------------------------------------- users

class User(ABC):
    """Shared identity and authentication for every actor."""

    def __init__(self, name: str, password: str, prefix: str) -> None:
        self.id = _next_id(prefix)
        self.name = name
        self._password_hash = self._hash(password)
        self.logged_in = False

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, password: str) -> bool:
        self.logged_in = self._hash(password) == self._password_hash
        return self.logged_in

    def logout(self) -> None:
        self.logged_in = False

    def _require_login(self) -> None:
        if not self.logged_in:
            raise PermissionError(f"{self.name} must be logged in")

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.id}, {self.name!r})"


class Patient(User):
    def __init__(self, name: str, password: str, email: str) -> None:
        super().__init__(name, password, "PAT")
        self.email = email
        self.problems: list[HealthProblem] = []
        self.inbox: list[Prescription] = []

    def post_problem(self, description: str) -> HealthProblem:
        self._require_login()
        problem = HealthProblem(self, description)
        self.problems.append(problem)
        return problem

    def receive_prescription(self, prescription: Prescription) -> None:
        self.inbox.append(prescription)

    def pay(self, prescription: Prescription, method: PaymentMethod) -> Payment:
        self._require_login()
        if prescription.problem.patient is not self:
            raise ValueError("cannot pay someone else's prescription")
        payment = Payment(prescription, prescription.fee, method)
        payment.process()
        return payment

    def history(self) -> list[Prescription]:
        return [p for pb in self.problems for p in pb.prescriptions]


class Doctor(User):
    def __init__(self, name: str, password: str, specialty: str) -> None:
        super().__init__(name, password, "DOC")
        self.specialty = specialty
        self.balance = 0.0
        self.cases: list[HealthProblem] = []

    def review(self, problem: HealthProblem) -> None:
        self.cases.append(problem)
        problem.set_status(ProblemStatus.IN_REVIEW)

    def write_prescription(self, problem: HealthProblem, content: str,
                           fee: float, based_on: Prescription | None = None
                           ) -> Prescription:
        if problem not in self.cases:
            raise ValueError("problem is not assigned to this doctor")
        prescription = Prescription(problem, self, content, fee, based_on)
        problem.prescriptions.append(prescription)
        return prescription

    def receive_payment(self, amount: float) -> None:
        self.balance += amount


class Organizer(User):
    """Coordinates consultations and also acts as administrator."""

    def __init__(self, name: str, password: str, system: HospitalSystem) -> None:
        super().__init__(name, password, "ORG")
        self.system = system

    # --- admin role
    def register_patient(self, name: str, password: str, email: str) -> Patient:
        self._require_login()
        return self.system.add_user(Patient(name, password, email))

    def register_doctor(self, name: str, password: str, specialty: str) -> Doctor:
        self._require_login()
        return self.system.add_user(Doctor(name, password, specialty))

    # --- coordination role
    def consult(self, problem: HealthProblem, doctor: Doctor) -> None:
        self._require_login()
        problem.doctor = doctor
        doctor.review(problem)

    def send_prescription(self, prescription: Prescription) -> None:
        self._require_login()
        prescription.delivered_at = datetime.now()
        prescription.problem.set_status(ProblemStatus.RESOLVED)
        prescription.problem.patient.receive_prescription(prescription)

    def forward_payment(self, payment: Payment) -> None:
        self._require_login()
        payment.forward_to(payment.prescription.doctor)


class HospitalSystem:
    """The database the organizer maintains."""

    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    def add_user(self, user):
        self.users[user.id] = user
        return user

    def find(self, user_id: str) -> User:
        return self.users[user_id]


# ---------------------------------------------------------------- domain

class ProblemStatus(Enum):
    PENDING = "pending"
    IN_REVIEW = "in-review"
    RESOLVED = "resolved"


_ALLOWED = {
    ProblemStatus.PENDING: {ProblemStatus.IN_REVIEW},
    ProblemStatus.IN_REVIEW: {ProblemStatus.RESOLVED},
    ProblemStatus.RESOLVED: {ProblemStatus.IN_REVIEW},  # follow-up
}


class HealthProblem:
    def __init__(self, patient: Patient, description: str) -> None:
        self.id = _next_id("HP")
        self.patient = patient
        self.description = description
        self.status = ProblemStatus.PENDING
        self.created_at = datetime.now()
        self.doctor: Doctor | None = None
        self.prescriptions: list[Prescription] = []

    def set_status(self, new: ProblemStatus) -> None:
        if new is self.status:
            return
        if new not in _ALLOWED[self.status]:
            raise ValueError(f"{self.status.value} -> {new.value} not allowed")
        self.status = new


class Prescription:
    def __init__(self, problem: HealthProblem, doctor: Doctor, content: str,
                 fee: float, based_on: Prescription | None = None) -> None:
        if fee < 0:
            raise ValueError("fee must be positive")
        self.id = _next_id("RX")
        self.problem = problem
        self.doctor = doctor
        self.content = content
        self.fee = fee
        self.based_on = based_on  # reference to a past prescription
        self.created_at = datetime.now()
        self.delivered_at: datetime | None = None
        self.payment: Payment | None = None


# ---------------------------------------------------------------- payment
# Strategy pattern: Payment delegates the "how" to a PaymentMethod.

class PaymentMethod(ABC):
    @abstractmethod
    def charge(self, amount: float) -> str:
        """Collect the money and return a transaction reference."""


class CashPayment(PaymentMethod):
    def charge(self, amount: float) -> str:
        return f"CASH receipt {amount:.2f}"


class CheckPayment(PaymentMethod):
    def __init__(self, check_number: str, bank: str) -> None:
        self.check_number = check_number
        self.bank = bank

    def charge(self, amount: float) -> str:
        return f"CHECK #{self.check_number} ({self.bank}) {amount:.2f}"


class CreditCardPayment(PaymentMethod):
    def __init__(self, card_number: str, expiry: str) -> None:
        if len(card_number) < 12 or not card_number.isdigit():
            raise ValueError("invalid card number")
        self.last4 = card_number[-4:]  # never keep the full number
        self.expiry = expiry

    def charge(self, amount: float) -> str:
        return f"CARD ****{self.last4} {amount:.2f}"


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FORWARDED = "forwarded"


class Payment:
    def __init__(self, prescription: Prescription, amount: float,
                 method: PaymentMethod) -> None:
        if prescription.payment is not None:
            raise ValueError("prescription already paid")
        if prescription.delivered_at is None:
            raise ValueError("prescription not delivered yet")
        if amount != prescription.fee:
            raise ValueError(f"amount {amount} != fee {prescription.fee}")
        self.id = _next_id("PAY")
        self.prescription = prescription
        self.amount = amount
        self.method = method
        self.status = PaymentStatus.PENDING
        self.reference: str | None = None
        self.paid_at: datetime | None = None
        self.forwarded_at: datetime | None = None

    def process(self) -> None:
        self.reference = self.method.charge(self.amount)  # polymorphic call
        self.paid_at = datetime.now()
        self.status = PaymentStatus.COMPLETED
        self.prescription.payment = self

    def forward_to(self, doctor: Doctor) -> None:
        if self.status is not PaymentStatus.COMPLETED:
            raise ValueError(f"cannot forward a {self.status.value} payment")
        doctor.receive_payment(self.amount)
        self.forwarded_at = datetime.now()
        self.status = PaymentStatus.FORWARDED


# ---------------------------------------------------------------- demo

def main() -> None:
    system = HospitalSystem()
    admin = system.add_user(Organizer("Olivia", "admin", system))
    admin.login("admin")

    # 1. registration
    alice = admin.register_patient("Alice", "pw", "alice@mail.com")
    house = admin.register_doctor("Dr House", "vicodin", "diagnostics")
    print("registered:", alice, house)

    # 2. consultation
    alice.login("pw")
    problem = alice.post_problem("Headache for 3 days")
    admin.consult(problem, house)
    rx = house.write_prescription(problem, "Paracetamol 1g x3/day", fee=25.0)
    admin.send_prescription(rx)
    print(f"{problem.id} status={problem.status.value}, inbox={len(alice.inbox)}")

    # 3. payment
    payment = alice.pay(rx, CreditCardPayment("4970101234567890", "12/28"))
    admin.forward_payment(payment)
    print(f"{payment.reference} -> {payment.status.value}, "
          f"{house.name} balance={house.balance}")


if __name__ == "__main__":
    main()
