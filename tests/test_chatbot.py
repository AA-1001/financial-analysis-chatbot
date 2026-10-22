"""Regression and input-validation tests for the financial chatbot."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from chatbot import DATA_PATH, METRICS, QUESTIONS, load_data, simple_chatbot


class FinancialChatbotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data()

    def test_dataset_complete(self):
        self.assertEqual(len(self.data), 9)
        self.assertEqual(set(self.data["Company"]), {"Apple", "Microsoft", "Tesla"})
        self.assertEqual(set(self.data["Fiscal Year"]), {2023, 2024, 2025})
        self.assertFalse(self.data[list(METRICS)].isna().any().any())

    def test_all_supported_queries_all_company_year_combinations(self):
        for company in ("Apple", "Microsoft", "Tesla"):
            for year in (2023, 2024, 2025):
                for question in QUESTIONS:
                    with self.subTest(company=company, year=year, question=question):
                        answer = simple_chatbot(question, company, str(year), self.data)
                        self.assertTrue(answer)
                        self.assertNotIn("Sorry", answer)
                        self.assertIn(company, answer)

    def test_apple_2025_revenue(self):
        self.assertIn("$416,161 million", simple_chatbot(QUESTIONS[0], "Apple", "2025", self.data))

    def test_microsoft_2025_operating_cash_flow(self):
        self.assertIn("$136,162 million", simple_chatbot(QUESTIONS[3], "Microsoft", 2025, self.data))

    def test_tesla_2025_net_income_change(self):
        answer = simple_chatbot(QUESTIONS[4], "Tesla", 2025, self.data)
        self.assertIn("decreased", answer)
        self.assertIn("$3,298 million", answer)
        self.assertIn("-46.11%", answer)

    def test_apple_2024_assets_and_liabilities(self):
        answer = simple_chatbot(QUESTIONS[2], "Apple", 2024, self.data)
        self.assertIn("$364,980 million", answer)
        self.assertIn("$308,030 million", answer)

    def test_2023_no_prior_year(self):
        answer = simple_chatbot(QUESTIONS[4], "Microsoft", 2023, self.data)
        self.assertIn("cannot be calculated", answer)

    def test_case_whitespace_and_punctuation(self):
        answer = simple_chatbot("   WHAT   IS THE TOTAL REVENUE???  ", "apple", "2025", self.data)
        self.assertIn("$416,161 million", answer)

    def test_unsupported_question(self):
        answer = simple_chatbot("What will the share price be?", "Tesla", 2025, self.data)
        self.assertIn("five predefined questions", answer)

    def test_non_string_question(self):
        answer = simple_chatbot(None, "Tesla", 2025, self.data)
        self.assertIn("five predefined questions", answer)

    def test_invalid_company(self):
        answer = simple_chatbot(QUESTIONS[0], "Amazon", 2025, self.data)
        self.assertIn("Company not found", answer)

    def test_invalid_year(self):
        answer = simple_chatbot(QUESTIONS[0], "Apple", "2024.5", self.data)
        self.assertIn("Invalid fiscal year", answer)

    def test_unicode_digit_year_rejected(self):
        answer = simple_chatbot(QUESTIONS[0], "Apple", "²⁰²⁵", self.data)
        self.assertIn("Invalid fiscal year", answer)

    def test_unavailable_year(self):
        answer = simple_chatbot(QUESTIONS[0], "Apple", 2026, self.data)
        self.assertIn("No financial data", answer)

    def test_zero_base_yoy(self):
        data = self.data.copy()
        data.loc[(data["Company"] == "Tesla") & (data["Fiscal Year"] == 2024), "Net Income"] = 0
        answer = simple_chatbot(QUESTIONS[4], "Tesla", 2025, data)
        self.assertIn("zero base", answer)
        self.assertNotIn("%", answer)

    def test_unchanged_yoy(self):
        data = self.data.copy()
        data.loc[(data["Company"] == "Tesla") & (data["Fiscal Year"] == 2025), "Net Income"] = 7153
        answer = simple_chatbot(QUESTIONS[4], "Tesla", 2025, data)
        self.assertIn("remained unchanged", answer)
        self.assertIn("+0.00%", answer)

    def test_negative_base_yoy(self):
        data = self.data.copy()
        data.loc[(data["Company"] == "Tesla") & (data["Fiscal Year"] == 2024), "Net Income"] = -100
        data.loc[(data["Company"] == "Tesla") & (data["Fiscal Year"] == 2025), "Net Income"] = 50
        answer = simple_chatbot(QUESTIONS[4], "Tesla", 2025, data)
        self.assertIn("increased by $150 million (+150.00%)", answer)

    def _load_modified(self, modify):
        data = self.data.copy()
        modify(data)
        with TemporaryDirectory() as folder:
            path = Path(folder) / "data.csv"
            data.to_csv(path, index=False)
            return load_data(path)

    def test_duplicate_rows_rejected(self):
        data = pd.concat([self.data, self.data.iloc[[0]]], ignore_index=True)
        with TemporaryDirectory() as folder:
            path = Path(folder) / "duplicate.csv"
            data.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "Duplicate company-year"):
                load_data(path)

    def test_duplicate_company_case_rejected(self):
        data = self.data.copy()
        data.loc[0, "Company"] = data.loc[0, "Company"].lower()
        data = pd.concat([data, self.data.iloc[[0]]], ignore_index=True)
        with TemporaryDirectory() as folder:
            path = Path(folder) / "duplicate_case.csv"
            data.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "Duplicate company-year"):
                load_data(path)

    def test_missing_values_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing financial values"):
            self._load_modified(lambda data: data.__setitem__("Net Income", data["Net Income"].mask(data.index == 0)))

    def test_missing_column_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "missing_column.csv"
            self.data.drop(columns=["Total Revenue"]).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "Missing required data columns"):
                load_data(path)

    def test_blank_company_rejected(self):
        with self.assertRaisesRegex(ValueError, "Company names cannot be blank"):
            self._load_modified(lambda data: data.__setitem__("Company", data["Company"].mask(data.index == 0, "   ")))

    def test_fractional_fiscal_year_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly four digits"):
            self._load_modified(lambda data: data.__setitem__("Fiscal Year", data["Fiscal Year"].mask(data.index == 0, "2024.5")))

    def test_nonfinite_metric_rejected(self):
        # Write a non-finite token directly rather than asking pandas to
        # serialise infinity, which can issue a nonessential runtime warning.
        with TemporaryDirectory() as folder:
            path = Path(folder) / "infinity.csv"
            contents = DATA_PATH.read_text(encoding="utf-8")
            contents = contents.replace(",72361,", ",inf,", 1)
            path.write_text(contents, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-finite"):
                load_data(path)

    def test_source_urls_and_units(self):
        self.assertTrue(self.data["Source Filing"].str.startswith("https://www.sec.gov/").all())
        self.assertEqual(set(self.data["Units"]), {"USD millions"})
        self.assertTrue(DATA_PATH.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
