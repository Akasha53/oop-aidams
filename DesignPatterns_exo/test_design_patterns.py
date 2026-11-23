import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import mock_open, patch

import adapter_report as ad
import builder_employee as bd
import decorator_order as dec
import factory_payment as fac
import singleton_config as sg
import strategy_report as st
import template_etl as tpl

CARD = {"card_number": "1234567890123456", "cvv": "123"}


class FactoryTest(unittest.TestCase):
    def setUp(self):
        self.factory = fac.PaymentFactory()

    def test_returns_the_right_processor(self):
        self.assertIsInstance(self.factory.get_processor("paypal"), fac.PayPalProcessor)
        self.assertIsInstance(self.factory.get_processor("credit_card"), fac.PaymentProcessor)

    def test_fees_are_unchanged(self):
        card = self.factory.get_processor("credit_card").process(100.0, CARD)
        bank = self.factory.get_processor("bank_transfer").process(100.0, {"iban": "FR7630006000011234"})
        paypal = self.factory.get_processor("paypal").process(100.0, {"email": "a@b.fr"})
        self.assertEqual((card["fee"], card["amount"]), (2.9, 102.9))
        self.assertEqual(bank["amount"], 101.5)
        self.assertEqual(paypal["fee"], 3.7)

    def test_invalid_details(self):
        result = self.factory.get_processor("credit_card").process(100.0, {"card_number": "123"})
        self.assertEqual(result, {"success": False, "error": "Invalid card number or CVV"})
        self.assertFalse(fac.BankTransferProcessor().validate({}))

    def test_unknown_type(self):
        with self.assertRaises(ValueError):
            self.factory.get_processor("cheque")

    def test_new_method_without_modifying_the_factory(self):
        result = self.factory.get_processor("crypto").process(100.0, {"wallet": "0x" + "a" * 40})
        self.assertEqual(result["amount"], 101.0)

        class GiftCard(fac.PaymentProcessor):
            method, error = "gift_card", "Invalid code"

            def validate(self, details):
                return bool(details.get("code"))

            def process(self, amount, details):
                return self._success(amount, 0) if self.validate(details) else self._failure()

        fac.PaymentFactory.register("gift_card", GiftCard)
        self.addCleanup(fac.PaymentFactory._processors.pop, "gift_card")
        self.assertTrue(self.factory.get_processor("gift_card").process(20, {"code": "X"})["success"])


class BuilderTest(unittest.TestCase):
    def test_fluent_build(self):
        e = (bd.EmployeeBuilder().with_name("John", "Doe").with_email("john.doe@company.com")
             .with_job("Engineering", "Senior Developer", 75000)
             .with_equipment(laptop=True, parking=False).with_access(vpn=True, admin=True)
             .build())
        self.assertIsInstance(e, bd.Employee)
        self.assertEqual((e.first_name, e.salary), ("John", 75000))
        self.assertTrue(e.has_laptop and e.has_vpn_access and e.has_admin_rights)
        self.assertFalse(e.has_parking)
        self.assertEqual(e.contract_type, "permanent")

    def test_presets(self):
        dev = bd.DeveloperBuilder("John", "Doe", "john.doe@company.com").build()
        senior = bd.DeveloperBuilder("Ann", "Lee", "ann@company.com", senior=True).build()
        intern = bd.InternBuilder("Jane", "Smith", "jane@company.com", "Marketing", 42).build()
        self.assertTrue(dev.has_vpn_access)
        self.assertFalse(dev.has_admin_rights)
        self.assertTrue(senior.has_admin_rights)  # the rule lives in the preset
        self.assertEqual((intern.contract_type, intern.manager_id), ("internship", 42))

    def test_preset_can_be_changed(self):
        dev = bd.DeveloperBuilder("John", "Doe", "j@company.com").with_office("Lyon").build()
        self.assertEqual(dev.office_location, "Lyon")

    def test_validation(self):
        with self.assertRaises(ValueError):
            bd.EmployeeBuilder().with_name("John", "Doe").with_email("no-at").build()
        with self.assertRaises(ValueError):
            bd.EmployeeBuilder().with_name("John", "Doe").with_email("j@x.fr").build()  # no job
        with self.assertRaises(ValueError):
            bd.DeveloperBuilder("A", "B", "a@b.fr").with_job("IT", "Dev", -1).build()


class SingletonTest(unittest.TestCase):
    def setUp(self):
        sg.ConfigManager.reset()
        self.addCleanup(sg.ConfigManager.reset)

    def test_same_instance(self):
        self.assertIs(sg.ConfigManager.get_instance(), sg.ConfigManager.get_instance())

    def test_file_read_only_once(self):
        fake_file = mock_open(read_data=json.dumps({"app": {"name": "Demo"}}))
        with patch("builtins.open", fake_file):
            sg.ConfigManager.get_instance()
            sg.ConfigManager.get_instance()
            sg.start_application()
        fake_file.assert_called_once()

    def test_dotted_get(self):
        config = sg.ConfigManager.get_instance()
        self.assertEqual(config.get("database.port"), 5432)
        self.assertIs(config.get("app.debug"), True)
        self.assertIsNone(config.get("database.missing"))
        self.assertEqual(config.get("nope.nope", "default"), "default")

    def test_change_is_seen_everywhere(self):
        sg.ConfigManager.get_instance().set("database.host", "db.prod")
        self.assertIn("db.prod:5432", sg.connect_database())


class AdapterTest(unittest.TestCase):
    def setUp(self):
        self.adapter = ad.LegacyReportAdapter(ad.LegacyReportGenerator())

    def test_xml_becomes_json(self):
        data = {"total_sales": 150000, "orders": 1234, "avg_order": 121.55}
        self.assertEqual(json.loads(self.adapter.generate(data)), data)

    def test_implements_the_interface(self):
        self.assertIsInstance(self.adapter, ad.ReportGeneratorInterface)

    def test_dashboard_accepts_the_adapter(self):
        out = io.StringIO()
        with redirect_stdout(out):
            ad.show_report(self.adapter, {"low_stock": 45, "status": "ok"})
        self.assertIn("low_stock: 45", out.getvalue())
        self.assertIn("status: ok", out.getvalue())


class DecoratorTest(unittest.TestCase):
    def test_base_order(self):
        self.assertEqual(dec.BaseOrder(100).get_cost(), 100)

    def test_same_total_as_old_code(self):
        order = dec.BaseOrder(100.0)
        for wrapper in (dec.ExpressShippingDecorator, dec.InsuranceDecorator, dec.GiftWrapDecorator):
            order = wrapper(order)
        order = dec.PremiumMemberDecorator(dec.DiscountDecorator(order, percent=15))
        # old calculate_total(all flags, 15%): (100 + 15 + 5 + 5) * 0.85 * 0.90
        self.assertAlmostEqual(order.get_cost(), 95.625)
        self.assertEqual(len(order.get_description().splitlines()), 6)

    def test_wrapping_order_is_calculation_order(self):
        discount_first = dec.ExpressShippingDecorator(dec.DiscountDecorator(dec.BaseOrder(100), 10))
        shipping_first = dec.DiscountDecorator(dec.ExpressShippingDecorator(dec.BaseOrder(100)), 10)
        self.assertAlmostEqual(discount_first.get_cost(), 105.0)
        self.assertAlmostEqual(shipping_first.get_cost(), 103.5)


DATA = [{"name": "Sales Q1", "value": 15000}, {"name": "Sales Q2", "value": 18000}]


class StrategyTest(unittest.TestCase):
    def setUp(self):
        self.generator = st.ReportGenerator(DATA)

    def test_switch_format_at_runtime(self):
        self.generator.set_strategy(st.CSVFormatStrategy())
        self.assertEqual(self.generator.generate_report(),
                         "name,value\nSales Q1,15000\nSales Q2,18000\n")
        self.generator.set_strategy(st.JSONFormatStrategy())
        self.assertEqual(json.loads(self.generator.generate_report()), DATA)

    def test_pdf_and_excel(self):
        pdf = st.PDFFormatStrategy().format(DATA)
        self.assertTrue(pdf.startswith("PDF REPORT\n" + "=" * 50))
        self.assertTrue(pdf.endswith("End of PDF Report"))
        self.assertIn("Sales Q2\t18000\n", st.ExcelFormatStrategy().format(DATA))

    def test_html_added_later(self):
        html = st.HTMLFormatStrategy().format([{"name": "<Q3>", "value": 1}])
        self.assertIn("<td>&lt;Q3&gt;</td>", html)

    def test_no_strategy(self):
        with self.assertRaises(ValueError):
            self.generator.generate_report()

    def test_save_uses_the_strategy_extension(self):
        self.generator.set_strategy(st.CSVFormatStrategy())
        with tempfile.TemporaryDirectory() as tmp:
            path = self.generator.save_report(str(Path(tmp) / "sales_report"))
            self.assertEqual(path.name, "sales_report.csv")
            self.assertTrue(path.read_text().startswith("name,value"))


class TemplateMethodTest(unittest.TestCase):
    def test_every_pipeline_runs_the_same_steps(self):
        for cls in (tpl.CSVPipeline, tpl.APIPipeline, tpl.DatabasePipeline, tpl.XMLPipeline):
            pipeline = cls("source")
            self.assertEqual(pipeline.run(), f"{cls.name} Pipeline finished")
            self.assertEqual(len(pipeline.loaded), 2)
            self.assertIsNone(pipeline.data)  # cleanup ran
            self.assertEqual(pipeline.logs[-1], "Cleanup complete")

    def test_transforms(self):
        csv, db = tpl.CSVPipeline("f.csv"), tpl.DatabasePipeline("db")
        csv.run()
        db.run()
        self.assertEqual(csv.loaded[0], {"id": 1, "name": "ALICE", "age": 30})
        self.assertAlmostEqual(db.loaded[0]["tax"], 240.0)

    def test_hook(self):
        api = tpl.APIPipeline("url")
        api.run()
        self.assertEqual([r["username"] for r in api.loaded], ["diana", "charlie"])
        self.assertEqual(api.loaded[0]["grade"], "A")

    def test_xml_pipeline(self):
        xml = tpl.XMLPipeline("orders.xml")
        xml.run()
        self.assertEqual(xml.loaded[0], {"order_id": 9001, "customer": "Eve", "total": 59.9})

    def test_invalid_record_still_cleans_up(self):
        class Broken(tpl.CSVPipeline):
            def transform(self, record):
                return {"age": 1}  # id and name missing

        pipeline = Broken("bad.csv")
        with self.assertRaises(ValueError):
            pipeline.run()
        self.assertEqual(pipeline.loaded, [])
        self.assertIsNone(pipeline.data)


if __name__ == "__main__":
    unittest.main()
