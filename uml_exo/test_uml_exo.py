import unittest

import abcd_records as ab
import hospital as h


class HospitalTest(unittest.TestCase):
    def setUp(self):
        self.system = h.HospitalSystem()
        self.admin = self.system.add_user(h.Organizer("O", "pw", self.system))
        self.admin.login("pw")
        self.pat = self.admin.register_patient("P", "pw", "p@x")
        self.doc = self.admin.register_doctor("D", "pw", "gp")
        self.pat.login("pw")

    def _prescribe(self, deliver=True):
        pb = self.pat.post_problem("cough")
        self.admin.consult(pb, self.doc)
        rx = self.doc.write_prescription(pb, "syrup", 30.0)
        if deliver:
            self.admin.send_prescription(rx)
        return pb, rx

    def test_full_flow(self):
        pb, rx = self._prescribe()
        self.assertIs(pb.status, h.ProblemStatus.RESOLVED)
        pay = self.pat.pay(rx, h.CashPayment())
        self.admin.forward_payment(pay)
        self.assertEqual(self.doc.balance, 30.0)
        self.assertIs(pay.status, h.PaymentStatus.FORWARDED)

    def test_login_required(self):
        self.pat.logout()
        with self.assertRaises(PermissionError):
            self.pat.post_problem("x")

    def test_wrong_password(self):
        self.assertFalse(self.pat.login("bad"))

    def test_cannot_pay_twice_or_before_delivery(self):
        _, rx = self._prescribe(deliver=False)
        with self.assertRaises(ValueError):
            self.pat.pay(rx, h.CashPayment())
        self.admin.send_prescription(rx)
        self.pat.pay(rx, h.CashPayment())
        with self.assertRaises(ValueError):
            self.pat.pay(rx, h.CashPayment())

    def test_cannot_forward_twice(self):
        _, rx = self._prescribe()
        pay = self.pat.pay(rx, h.CheckPayment("123", "LCL"))
        self.admin.forward_payment(pay)
        with self.assertRaises(ValueError):
            self.admin.forward_payment(pay)
        self.assertEqual(self.doc.balance, 30.0)

    def test_status_transitions(self):
        pb = self.pat.post_problem("x")
        with self.assertRaises(ValueError):
            pb.set_status(h.ProblemStatus.RESOLVED)  # skip review

    def test_card_keeps_only_last4(self):
        card = h.CreditCardPayment("4970101234567890", "12/28")
        self.assertEqual(card.last4, "7890")
        self.assertFalse(hasattr(card, "card_number"))

    def test_prescription_history(self):
        pb, rx1 = self._prescribe()
        self.admin.consult(pb, self.doc)  # follow-up, back to in-review
        rx2 = self.doc.write_prescription(pb, "stronger", 40.0, based_on=rx1)
        self.assertIs(rx2.based_on, rx1)
        self.assertEqual(self.pat.history(), [rx1, rx2])


class AbcdTest(unittest.TestCase):
    def setUp(self):
        self.records = ab.DailyRecordsFile()
        self.royal = ab.RoyalMember("R", "addr")
        self.regular = ab.RegularMember("G", "addr")
        members = {m.member_id: m for m in (self.royal, self.regular)}
        self.clerk = ab.OrderProcessingClerk("C", members, self.records)
        self.cashier = ab.CollectionDepartmentClerk("K")
        self.cd = ab.CD("1", "A", "x", 10.0, stock=3)
        self.missing = ab.CD("2", "B", "y", 20.0, stock=0)

    def test_royal_scenario(self):
        order = self.royal.place_order([(self.cd, 1), (self.missing, 1)])
        inv, ship = self.clerk.process_order(order)
        self.assertEqual(inv.amount, 9.0)  # 10 - 10 %
        self.assertEqual(len(order.shippable_lines()), 1)
        self.assertEqual(len(self.clerk.reorders), 1)
        self.assertIn("PRIORITY", ship.print())
        self.cashier.collect(inv, ab.Check(9.0, "555", "SG"))
        self.assertIs(order.status, ab.OrderStatus.PAID)
        self.assertEqual(self.cd.stock, 2)

    def test_regular_cannot_order_unavailable(self):
        order = self.regular.place_order([(self.missing, 1)])
        with self.assertRaises(ValueError):
            self.clerk.process_order(order)
        self.assertIs(order.status, ab.OrderStatus.REJECTED)

    def test_unknown_member_rejected(self):
        stranger = ab.RegularMember("S", "addr")
        with self.assertRaises(PermissionError):
            self.clerk.process_order(stranger.place_order([(self.cd, 1)]))

    def test_non_member_gets_form(self):
        nm = ab.NonMember("N", "addr")
        self.assertFalse(self.clerk.verify_membership(nm))
        form = self.clerk.send_application(nm)
        self.assertIs(nm.application, form)

    def test_payment_types(self):
        order = self.regular.place_order([(self.cd, 2)])
        inv, _ = self.clerk.process_order(order)
        with self.assertRaises(ValueError):
            self.cashier.collect(inv, ab.Cash(5.0))  # wrong amount
        with self.assertRaises(ValueError):
            self.cashier.collect(inv, ab.BankDraft(20.0, "", "BNP"))  # invalid draft
        self.cashier.collect(inv, ab.BankDraft(20.0, "D1", "BNP"))
        with self.assertRaises(ValueError):
            self.cashier.collect(inv, ab.Cash(20.0))  # already paid

    def test_daily_records(self):
        self.clerk.process_order(self.regular.place_order([(self.cd, 1)]))
        self.assertEqual(len(self.records.orders_of(self.regular.orders[0].date)), 1)


if __name__ == "__main__":
    unittest.main()
