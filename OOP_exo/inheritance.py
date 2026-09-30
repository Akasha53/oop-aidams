"""OOP practice - Inheritance (slide 67)."""
from __future__ import annotations


# Problem 1
class Vehicle:
    def drive(self) -> str:
        return "Driving a vehicle"


class Car(Vehicle):
    def drive(self) -> str:
        return "Driving a car"


class Bicycle(Vehicle):
    def drive(self) -> str:
        return "Riding a bicycle"


# Problem 2
class Person:
    def __init__(self, name: str, age: int, address: str) -> None:
        self.name = name
        self.age = age
        self.address = address

    def introduce(self) -> str:
        return f"Hi, I'm {self.name}, {self.age} years old, living at {self.address}."


class Student(Person):
    def __init__(self, name: str, age: int, address: str, field_of_study: str) -> None:
        super().__init__(name, age, address)
        self.field_of_study = field_of_study

    def introduce(self) -> str:
        return f"{super().introduce()} I study {self.field_of_study}."


class Employee(Person):
    def __init__(self, name: str, age: int, address: str, company: str) -> None:
        super().__init__(name, age, address)
        self.company = company

    def introduce(self) -> str:
        return f"{super().introduce()} I work at {self.company}."


# Problem 3
class BankAccount:
    def __init__(self, account_number: str, balance: float = 0.0) -> None:
        self.account_number = account_number
        self.balance = balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("deposit must be positive")
        self.balance += amount

    def withdraw(self, amount: float) -> bool:
        if amount <= 0:
            raise ValueError("withdrawal must be positive")
        if amount > self.balance:
            return False
        self.balance -= amount
        return True

    def transfer(self, destination: BankAccount, amount: float) -> bool:
        if not self.withdraw(amount):
            return False
        destination.deposit(amount)
        return True


class SavingsAccount(BankAccount):
    def __init__(self, account_number: str, balance: float = 0.0,
                 interest_rate: float = 0.02) -> None:
        super().__init__(account_number, balance)
        self.interest_rate = interest_rate

    def add_interest(self) -> float:
        interest = self.balance * self.interest_rate
        self.balance += interest
        return interest

    def check_balance(self) -> float:
        return self.balance


if __name__ == "__main__":
    for v in (Vehicle(), Car(), Bicycle()):
        print(v.drive())
    for p in (Person("Ana", 30, "Paris"),
              Student("Bob", 20, "Lyon", "data science"),
              Employee("Cleo", 40, "Lille", "Airbus")):
        print(p.introduce())
    checking = BankAccount("FR01", 100)
    savings = SavingsAccount("FR02", 1000, 0.03)
    print(checking.transfer(savings, 150), checking.transfer(savings, 50))
    savings.add_interest()
    print(checking.balance, savings.check_balance())
