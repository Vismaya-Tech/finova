

# Power BI Financial Data Input

This project generates a **Power BI–ready CSV** by automatically extracting full financial data from **Screener.in** using just a company name.

### What it produces

A **single normalized CSV** with this fixed schema:

```
Company, Symbol, Statement, Section, Metric, Year, Value, Unit, Source
```

Each row = **one metric for one year**
This format is **ideal for Power BI time-series charts, filters, and comparisons**.

### Why this works for Power BI

* Handles **large Screener datasets**
* No schema changes when years increase
* Easy slicing by Company, Metric, Year
* Direct import — no manual cleanup

### Usage

```bash
python financial_data_pipeline.py "ambuja"
```

Output:

```
screener_normalized_data.csv
```

Import the CSV into Power BI and build dashboards immediately.

---
