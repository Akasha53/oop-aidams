import unittest

import inheritance as inh
import operator_overloading as ov


class OperatorTest(unittest.TestCase):
    def test_complex(self):
        self.assertEqual(ov.Complex(1, 2) + ov.Complex(3, 4), ov.Complex(4, 6))
        self.assertEqual(ov.Complex(1, 2) - ov.Complex(3, 4), ov.Complex(-2, -2))

    def test_person(self):
        a, b = ov.Person("A", 30, "F"), ov.Person("B", 25, "M")
        self.assertTrue(a > b)
        self.assertFalse(b > a)
        self.assertTrue(b < a)  # Python reflects > for free

    def test_vector_dot(self):
        self.assertEqual(ov.Vector(1, 2, 3) * ov.Vector(4, 5, 6), 32)

    def test_circle(self):
        small, big = ov.Circle(1), ov.Circle(2)
        self.assertTrue(small < big and small <= big and big > small and big >= small)
        self.assertTrue(small == ov.Circle(1) and small != big)
        self.assertFalse(small == "circle")

    def test_point(self):
        self.assertEqual(ov.Point(3, 4), ov.Point(0, 5))  # both at distance 5
        self.assertTrue(ov.Point(1, 1) < ov.Point(3, 4))
        self.assertTrue(ov.Point(3, 4) >= ov.Point(-5, 0))
        self.assertFalse(ov.Point(3, 4) > ov.Point(0, 5))

    def test_matrix(self):
        a = ov.Matrix([[1, 2], [3, 4]])
        b = ov.Matrix([[5, 6], [7, 8]])
        self.assertEqual(a * b, ov.Matrix([[19, 22], [43, 50]]))
        self.assertEqual((ov.Matrix([[1, 2, 3]]) * ov.Matrix([[1], [1], [1]])).rows, [[6]])
        with self.assertRaises(ValueError):
            a * ov.Matrix([[1, 2, 3]])


class InheritanceTest(unittest.TestCase):
    def test_vehicles(self):
        self.assertEqual([v.drive() for v in (inh.Vehicle(), inh.Car(), inh.Bicycle())],
                         ["Driving a vehicle", "Driving a car", "Riding a bicycle"])

    def test_introduce(self):
        s = inh.Student("B", 20, "Lyon", "maths")
        e = inh.Employee("C", 40, "Lille", "Airbus")
        self.assertIsInstance(s, inh.Person)
        self.assertIn("maths", s.introduce())
        self.assertIn("Airbus", e.introduce())

    def test_transfer(self):
        src, dst = inh.BankAccount("1", 100), inh.SavingsAccount("2", 0, 0.1)
        self.assertTrue(src.transfer(dst, 60))
        self.assertFalse(src.transfer(dst, 60))  # insufficient
        self.assertEqual((src.balance, dst.check_balance()), (40, 60))

    def test_interest(self):
        acc = inh.SavingsAccount("2", 200, 0.05)
        self.assertEqual(acc.add_interest(), 10)
        self.assertEqual(acc.check_balance(), 210)


if __name__ == "__main__":
    unittest.main()
