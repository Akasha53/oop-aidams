"""OOP practice - Operator overloading (slide 67)."""
from __future__ import annotations

import math
from functools import total_ordering


# Problem 1
class Complex:
    def __init__(self, real: float, imag: float = 0.0) -> None:
        self.real = real
        self.imag = imag

    def __add__(self, other: Complex) -> Complex:
        return Complex(self.real + other.real, self.imag + other.imag)

    def __sub__(self, other: Complex) -> Complex:
        return Complex(self.real - other.real, self.imag - other.imag)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Complex):
            return NotImplemented
        return (self.real, self.imag) == (other.real, other.imag)

    def __repr__(self) -> str:
        sign = "+" if self.imag >= 0 else "-"
        return f"({self.real} {sign} {abs(self.imag)}i)"


# Problem 2
class Person:
    def __init__(self, name: str, age: int, gender: str) -> None:
        self.name = name
        self.age = age
        self.gender = gender

    def __gt__(self, other: Person) -> bool:
        return self.age > other.age

    def __repr__(self) -> str:
        return f"Person({self.name!r}, {self.age})"


# Problem 4
class Vector:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

    def __mul__(self, other: Vector) -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y}, {self.z})"


# Problem 5: all six operators written by hand
class Circle:
    def __init__(self, radius: float) -> None:
        if radius < 0:
            raise ValueError("radius must be >= 0")
        self.radius = radius

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Circle):
            return NotImplemented
        return self.radius == other.radius

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        return result if result is NotImplemented else not result

    def __lt__(self, other: Circle) -> bool:
        return self.radius < other.radius

    def __le__(self, other: Circle) -> bool:
        return self.radius <= other.radius

    def __gt__(self, other: Circle) -> bool:
        return self.radius > other.radius

    def __ge__(self, other: Circle) -> bool:
        return self.radius >= other.radius

    def __repr__(self) -> str:
        return f"Circle({self.radius})"


# Problem 6: __eq__ + __lt__, total_ordering derives the other four
@total_ordering
class Point:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def distance(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return math.isclose(self.distance(), other.distance())

    def __lt__(self, other: Point) -> bool:
        return self.distance() < other.distance() and self != other

    def __hash__(self) -> int:
        return hash(round(self.distance(), 9))

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"


# Problem 7
class Matrix:
    def __init__(self, rows: list[list[float]]) -> None:
        if not rows or any(len(r) != len(rows[0]) for r in rows):
            raise ValueError("matrix must be non-empty and rectangular")
        self.rows = [list(r) for r in rows]

    @property
    def shape(self) -> tuple[int, int]:
        return len(self.rows), len(self.rows[0])

    def __mul__(self, other: Matrix) -> Matrix:
        n, m = self.shape
        m2, p = other.shape
        if m != m2:
            raise ValueError(f"cannot multiply {self.shape} by {other.shape}")
        return Matrix([
            [sum(self.rows[i][k] * other.rows[k][j] for k in range(m))
             for j in range(p)]
            for i in range(n)
        ])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return NotImplemented
        return self.rows == other.rows

    def __repr__(self) -> str:
        return f"Matrix({self.rows})"


if __name__ == "__main__":
    print(Complex(1, 2) + Complex(3, -5), Complex(1, 2) - Complex(3, -5))
    print(Person("Ana", 30, "F") > Person("Bob", 25, "M"))
    print(Vector(1, 2, 3) * Vector(4, 5, 6))
    print(Circle(2) <= Circle(3), Circle(2) != Circle(2))
    print(Point(3, 4) == Point(0, 5), Point(1, 1) < Point(3, 4))
    print(Matrix([[1, 2], [3, 4]]) * Matrix([[5, 6], [7, 8]]))
