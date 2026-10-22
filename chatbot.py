"""Rule-based financial question answering over curated SEC Form 10-K data.

The dataset covers Apple, Microsoft and Tesla, fiscal years 2023–2025.
All statement amounts are expressed in USD millions.
"""

from pathlib import Path
import math
import re

import pandas as pd


DATA_PATH = Path(__file__).resolve().parent / "data" / "financial_data_2023_2025.csv"

QUESTIONS = (
    "What is the total revenue?",
    "What is the net income?",
    "What are the total assets and total liabilities?",
    "What is the operating cash flow?",
    "How has net income changed over the last year?",
)

METRICS = (
    "Total Revenue",
    "Net Income",
    "Total Assets",
    "Total Liabilities",
    "Operating Cash Flow",
)

REQUIRED_COLUMNS = {"Company", "Fiscal Year", *METRICS}


def load_data(csv_path=DATA_PATH):
    """Load financial records; reject incomplete or ambiguous company-year data."""
    # Read fiscal years as strings first: converting 2024.5 directly to int
    # could silently turn it into the valid (but incorrect) year 2024.
    data = pd.read_csv(csv_path, dtype={"Fiscal Year": "string", "Company": "string"})
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required data columns: {sorted(missing_columns)}")

    if data.empty:
        raise ValueError("The financial dataset is empty.")

    if data[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("Missing financial values found; check the source CSV.")

    data["Company"] = data["Company"].str.strip()
    if data["Company"].eq("").any():
        raise ValueError("Company names cannot be blank.")

    fiscal_year = data["Fiscal Year"].str.strip()
    if not fiscal_year.str.fullmatch(r"[0-9]{4}").all():
        raise ValueError("Fiscal Year must contain exactly four digits per record.")
    data["Fiscal Year"] = fiscal_year.astype(int)

    for metric in METRICS:
        data[metric] = pd.to_numeric(data[metric], errors="raise")
    if not data[list(METRICS)].apply(lambda column: column.map(math.isfinite)).all().all():
        raise ValueError("Missing or non-finite financial values found; check the source CSV.")

    if data.assign(_company_key=data["Company"].str.casefold()).duplicated(
        subset=["_company_key", "Fiscal Year"]
    ).any():
        raise ValueError("Duplicate company-year records found in the CSV.")

    return data


def normalize_question(question):
    """Normalise punctuation, spacing and case (not natural-language parsing)."""
    if not isinstance(question, str):
        return ""
    return re.sub(r"\s+", " ", question.strip().casefold()).rstrip("?.! ")


def simple_chatbot(user_query, company, fiscal_year, data):
    """Answer one of five fixed questions for a selected company and fiscal year."""
    normalized = normalize_question(user_query)
    if normalized not in {normalize_question(question) for question in QUESTIONS}:
        return "Sorry, I can only answer the five predefined questions. Type 'help' to see them."

    company_key = str(company).strip().casefold()
    matches = data.loc[data["Company"].str.casefold() == company_key]
    if matches.empty:
        return "Company not found. Please choose Apple, Microsoft or Tesla."

    year_text = str(fiscal_year).strip()
    if re.fullmatch(r"[0-9]{4}", year_text) is None:
        return "Invalid fiscal year. Please enter 2023, 2024 or 2025."
    year = int(year_text)

    current = matches.loc[matches["Fiscal Year"] == year]
    if current.empty:
        return f"No financial data is available for {matches.iloc[0]['Company']} in FY{year}."

    row = current.iloc[0]
    display_company = str(row["Company"])
    prefix = f"{display_company} FY{year}"

    if normalized == normalize_question(QUESTIONS[0]):
        return f"{prefix} total revenue was ${row['Total Revenue']:,.0f} million."

    if normalized == normalize_question(QUESTIONS[1]):
        return f"{prefix} net income was ${row['Net Income']:,.0f} million."

    if normalized == normalize_question(QUESTIONS[2]):
        return (
            f"{prefix} total assets were ${row['Total Assets']:,.0f} million "
            f"and total liabilities were ${row['Total Liabilities']:,.0f} million."
        )

    if normalized == normalize_question(QUESTIONS[3]):
        return (
            f"{prefix} net cash from operating activities "
            f"was ${row['Operating Cash Flow']:,.0f} million."
        )

    if normalized == normalize_question(QUESTIONS[4]):
        previous = matches.loc[matches["Fiscal Year"] == year - 1]
        if previous.empty:
            return (
                f"The year-over-year change in {display_company}'s FY{year} "
                "net income cannot be calculated because the preceding year's "
                "data is not included in this dataset."
            )

        old_income = float(previous.iloc[0]["Net Income"])
        new_income = float(row["Net Income"])
        difference = new_income - old_income
        direction = (
            "increased" if difference > 0 else
            "decreased" if difference < 0 else
            "remained unchanged"
        )

        if old_income == 0:
            return (
                f"{display_company} net income {direction} by "
                f"${abs(difference):,.0f} million from FY{year-1} to FY{year}. "
                "A percentage change cannot be calculated from a zero base."
            )

        # Using abs(previous) keeps direction meaningful if earlier income is negative.
        pct = difference / abs(old_income) * 100
        return (
            f"{display_company} net income {direction} by "
            f"${abs(difference):,.0f} million ({pct:+.2f}%) "
            f"from FY{year-1} (${old_income:,.0f} million) "
            f"to FY{year} (${new_income:,.0f} million)."
        )

    return "Sorry, I can only answer the five predefined questions."


def show_questions():
    """Display the supported question menu."""
    for number, question in enumerate(QUESTIONS, start=1):
        print(f"  {number}. {question}")


def main():
    """Run the interactive command-line chatbot."""
    try:
        data = load_data()
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        print(f"Could not load financial data: {exc}")
        return

    print("\nFinancial Analysis Chatbot | USD millions")
    print("Data: SEC Forms 10-K, fiscal years 2023–2025")
    print("Choose Apple, Microsoft or Tesla and a fiscal year.")

    try:
        company = input("Company: ").strip()
        year = input("Fiscal year (2023 / 2024 / 2025): ").strip()
        print("\nPredefined questions:")
        show_questions()
        print("Enter a question (or its number), 'help', 'change', or 'exit'.")

        while True:
            user_query = input("\nYou: ").strip()
            if user_query.casefold() in {"exit", "quit"}:
                print("Chatbot: Goodbye!")
                break
            if user_query.casefold() == "help":
                show_questions()
                continue
            if user_query.casefold() == "change":
                company = input("Company: ").strip()
                year = input("Fiscal year (2023 / 2024 / 2025): ").strip()
                continue
            if user_query in {"1", "2", "3", "4", "5"}:
                user_query = QUESTIONS[int(user_query) - 1]

            print("Chatbot:", simple_chatbot(user_query, company, year, data))
    except (KeyboardInterrupt, EOFError):
        print("\nChatbot: Goodbye!")


if __name__ == "__main__":
    main()
