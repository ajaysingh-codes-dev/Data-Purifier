# Data Purifier

Automated Data Cleaning & Preprocessing Pipeline built with Python and Pandas.

## Overview

Data Purifier is a Python-based ETL and data-cleaning tool designed to clean messy datasets from multiple sources such as:

- CSV files
- Excel files
- MySQL databases

The project automatically detects and fixes common data quality issues including:

- Missing values
- Duplicate records
- Invalid email data
- Incorrect numeric formats
- Date conversion issues
- Null-like values
- Inconsistent text formatting

Cleaned datasets are exported into structured Excel reports.

---

# Features

## Multi-Source Input
Supports:
- CSV
- Excel
- MySQL tables

## Data Cleaning
- Removes empty rows and columns
- Standardizes column names
- Cleans string formatting
- Converts null-like values to proper NaN

## Date Detection
Automatically detects and converts:
- date
- time
- dob
- created
- updated
- timestamp

columns into datetime format.

## Email Validation
- Detects email columns automatically
- Removes invalid/missing email rows
- Detects duplicate emails

## ID Detection
Automatically detects columns such as:
- id
- uuid
- guid
- serial
- key

and handles:
- missing IDs
- duplicate IDs

## Numeric Conversion
Converts values like:
- ₹5,000
- rs.2500
- 10k
- 2.5m
- one hundred

into proper numeric format.

## Smart Missing Value Filling
### Numeric Columns
- Filled using median

### Date Columns
- Filled using forward fill

### Object/String Columns
- Mode filling
- High-null columns filled with `"missing"`

## Excel Report Export
Exports:
- cleaned data
- incomplete records
- duplicate records
- fill logs

into separate Excel sheets.

# Author

Ajay Singh
