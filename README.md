# Financial Analysis Chatbot | Python & SEC 10-K Data

**A rule-based command-line chatbot for retrieving and comparing historical company financials.** The project converts selected financial statement figures into structured CSV data and makes them accessible through five predefined questions for **Apple, Microsoft and Tesla (FY2023–FY2025)**.

Rather than generating answers with a language model, the chatbot uses **Python, pandas and transparent lookup/calculation rules**. It demonstrates a small, explainable financial data workflow: curated financial records → validated dataset → question routing → calculated response.

> **Portfolio prototype:** Global Finance Corp. (GFC) is a fictional use case. This is not a commercial deployment, a generative AI system or a product affiliated with the companies analysed.

## At a glance

| Coverage | Details |
|---|---|
| Companies | Apple, Microsoft, Tesla |
| Financial periods | FY2023–FY2025 (9 company-year records) |
| Financial measures | Revenue, net income, assets, liabilities, operating cash flow |
| Interaction | Terminal / command line; five predefined questions |
| Additional calculation | Year-over-year net income change (absolute and percentage) |
| Data source | Curated figures from SEC Form 10-K annual filings |
| Technologies | Python, pandas, CSV, `pathlib`, `re`, `unittest` |

## Business problem and objective

Company financial statements contain useful performance information, but answering a straightforward question can still require finding a filing, locating the appropriate financial statement and checking its units and reporting period. This prototype makes a **limited set of recurring financial questions** faster to answer from a reviewed dataset.

The goal is to demonstrate how structured financial information can underpin an explainable, testable conversational interface without requiring an LLM. The application is intentionally small: it returns values for a selected company and fiscal year, and computes a year-over-year change when the preceding year is available.

## Features

- **Company/year selection:** choose Apple, Microsoft or Tesla and FY2023, FY2024 or FY2025.
- **Five question types:** retrieve revenue, net income, assets and liabilities, or operating cash flow; calculate year-over-year net income movement.
- **Input normalisation:** ignores casing, extra spacing and trailing question punctuation.
- **Data integrity checks:** rejects missing required data, invalid fiscal years, duplicate company-year entries and non-finite financial values.
- **Graceful limitations:** explains unavailable years, unsupported companies/questions and missing prior-year comparisons.
- **Simple interactive controls:** question numbers `1`–`5`, `help`, `change` and `exit`.
- **Automated tests:** exercise query routing, numerical values, year-over-year calculations and validation edge cases.

## Architecture

```text
financial-analysis-chatbot/
├── README.md
├── chatbot.py                       # CSV validation, query logic and terminal interface
├── requirements.txt                # pandas dependency
├── .gitignore
├── data/
│   └── financial_data_2023_2025.csv  # Nine records with SEC source URLs
└── tests/
    └── test_chatbot.py             # Standard-library unittest suite
```

**How a response is produced:**

1. `load_data()` loads the versioned CSV from `data/` using a path relative to `chatbot.py`.
2. Validation checks essential financial fields, numeric values and unique company-year records.
3. `simple_chatbot()` normalises the selected predefined question and retrieves the relevant row using pandas.
4. A small `if`-based routing function formats the requested amount or calculates the FY-over-FY net income change.
5. The terminal loop displays the answer and accepts another question or a change of company/year.

No model is trained, and there is no live SEC/API connection at runtime.

## Getting started

**Prerequisites:** Python 3.9+ and Git (Git is needed only for cloning).

```bash
git clone https://github.com/<YOUR_GITHUB_USERNAME>/financial-analysis-chatbot.git
cd financial-analysis-chatbot
```

Replace `<YOUR_GITHUB_USERNAME>` with the GitHub username when the repository is published. Alternatively, download and extract the repository ZIP, then open a terminal in the extracted folder.

Create a virtual environment and install the sole third-party dependency:

**Windows (PowerShell)**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python chatbot.py
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python chatbot.py
```

If PowerShell blocks activation, you can run `.venv\Scripts\python.exe chatbot.py` (and use the same executable with `-m pip`) without activating the environment.

## How to use

At startup, select a company and fiscal year. Enter one of the questions verbatim, or use its numbered shortcut:

| # | Supported question |
|---|---|
| 1 | What is the total revenue? |
| 2 | What is the net income? |
| 3 | What are the total assets and total liabilities? |
| 4 | What is the operating cash flow? |
| 5 | How has net income changed over the last year? |

Other terminal commands: `help` lists the questions, `change` selects a new company/year, and `exit` (or `quit`) closes the application.

### Verified sample interactions

**Apple, FY2025 — revenue**

```text
You: 1
Chatbot: Apple FY2025 total revenue was $416,161 million.
```

**Microsoft, FY2025 — operating cash flow**

```text
You: What is the operating cash flow?
Chatbot: Microsoft FY2025 net cash from operating activities was $136,162 million.
```

**Tesla, FY2025 — net income change**

```text
You: 5
Chatbot: Tesla net income decreased by $3,298 million (-46.11%) from FY2024 ($7,153 million) to FY2025 ($3,855 million).
```

**Microsoft, FY2023 — missing FY2022 comparison**

```text
You: 5
Chatbot: The year-over-year change in Microsoft's FY2023 net income cannot be calculated because the preceding year's data is not included in this dataset.
```

All amounts shown are **USD millions**, not raw dollars. For example, `$416,161 million` is approximately `$416.2 billion`.

## Financial data and methodology

The accompanying CSV contains **nine records**, one per company and fiscal year, with five financial statement metrics plus identifying and provenance fields:

| Field | Interpretation |
|---|---|
| `Company` | Company used to select a financial record |
| `Fiscal Year`, `Fiscal Year End` | Company's reported fiscal year and closing date |
| `Total Revenue` | Reported consolidated revenue / net sales |
| `Net Income` | Consolidated net income (not necessarily income attributable only to common shareholders) |
| `Total Assets`, `Total Liabilities` | Year-end balance-sheet totals |
| `Operating Cash Flow` | Net cash provided by operating activities |
| `Source Filing` | Official SEC filing URL for that company/year |
| `Units` | USD millions for all five measures |

These figures are **historical extracted records**, not live market data. Fiscal-year end dates differ: **Microsoft** ends in June, **Apple** in September and **Tesla** in December. Comparing their FY2025 records is not the same as comparing an identical 12-month calendar period.

### SEC source filings

All nine filing URLs are saved in `data/financial_data_2023_2025.csv`. Direct official filings for the latest covered year:

- [Apple FY2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
- [Microsoft FY2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm)
- [Tesla FY2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm)

The dataset's values are retained from the original curated extraction. They are not automatically downloaded or refreshed by the chatbot.

### Year-over-year calculation

For net income, when both the selected fiscal year and the preceding fiscal year exist:

```text
Absolute change = Current-year net income - Previous-year net income
Percentage change = Absolute change / abs(Previous-year net income) × 100
```

Using the absolute prior-year denominator preserves the sign of improvement/deterioration even if the prior year records a loss. If the previous value is zero, the chatbot reports the dollar change but does **not** claim a percentage change. FY2023 net-income YoY changes are unavailable because FY2022 is not included.

## Findings illustrated by the dataset

| Financial observation | FY2024 | FY2025 | Interpretation |
|---|---:|---:|---|
| Microsoft revenue | $245,122m | $281,724m | Increased **14.93%** |
| Apple net income | $93,736m | $112,010m | Increased **19.50%** |
| Tesla net income | $7,153m | $3,855m | Decreased **46.11%** |

These are **descriptive historical comparisons** calculated from the stored financial figures. They do not establish why changes occurred or predict future financial performance. The application only generates the net-income comparison interactively; the other observations are included as context for the dataset.

## Testing and validation

From the repository root, run:

```bash
python -m unittest discover -s tests -v
```

The automated suite exercises all **45 combinations** of three companies, three years and five supported questions, plus numerical spot checks, unsupported queries, boundary cases and malformed input files. The suite also tests zero and negative prior-year income when calculating percentage changes.

Test results should be produced by running the command locally rather than relying on a historical output log. The included dataset has exactly nine complete company-year records. Selected FY2025 values were also cross-checked against the cited SEC filings; this is **not** an independently automated audit of every SEC statement figure.

## Limitations

- **Rule-driven rather than generative:** only the five listed question forms are understood. There is no LLM, NLP intent classifier, model training or free-form reasoning.
- **Static data:** the chatbot cannot retrieve live filings, prices, news or other real-time financial information.
- **Limited coverage:** only three companies, FY2023–FY2025 and five financial measures are provided.
- **Comparability:** fiscal-year end dates differ, and financial statement definitions must be interpreted consistently.
- **No causal explanation:** financial movements are arithmetic observations, not estimates of the causes of performance changes.
- **Scope:** this educational portfolio prototype is not investment advice, an investor research platform or an endorsed company product.

## Future improvements

1. Introduce more flexible question interpretation, beginning with tested intent/keyword matching or NLP.
2. Expand company and metric coverage while retaining filing-level source references.
3. Automate ingestion and validation using SEC-accessible data, respecting access guidance and data provenance.
4. Add a lightweight interface and a small set of financial trend visualisations.
5. Consider LLM-assisted explanations **only after** implementing retrieval grounding, citations and safeguards against invented financial figures.

## Skills demonstrated

**Python programming · pandas · financial data preparation · CSV validation · relative-path file handling · business-rule implementation · YoY calculations · command-line interaction · automated unit testing · error handling · technical documentation · financial interpretation**

## Author

**[Your Name]** · [LinkedIn profile](https://www.linkedin.com/in/YOUR-PROFILE/) · [GitHub profile](https://github.com/YOUR_GITHUB_USERNAME)

*Personal portfolio project demonstrating the foundations of a structured financial question-answering system.*
