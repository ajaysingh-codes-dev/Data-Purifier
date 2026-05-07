import numpy as np
import pandas as pd
import mysql.connector
from word2number import w2n
import re

def read_csv(file):
    try:
        df = pd.read_csv(file)
        print("csv loaded successfully")
        return df
    except Exception as e:
        print(f"Error reading CSV: {e}")

def read_excel(file):
    try:
        df = pd.read_excel(file)
        print("excel loaded successfully")
        return df
    except Exception as e:
        print(f"Error reading EXCEL: {e}")

def read_sql():
    try:
        host = input("Enter MYSQL host name: ")
        user = input("Enter MYSQL user name: ")
        password = input("Enter MYSQL password: ")
        database = input("Enter your database name: ")
        table = input("Enter table name you want to clean: ")

        conn = mysql.connector.connect(host = host,
                                    user = user,
                                    password = password,
                                    database = database)
        query = f"SELECT * FROM `{table}`"
        df = pd.read_sql(query, conn)
        print("SQL Data Loaded Successfully")
        conn.close()
        return df
    except Exception as e:
        print(f"Database Error: {e}")

def strip_lower(df):
    try:
        df.columns = df.columns.str.strip().str.lower()
        null_values = ["nan", "n/a", "na", "none", "null", "", "--", "missing", "?"]
        df_col = df.select_dtypes(include=["object", "string"])
        for col in df_col:
            df[col] = df[col].str.lower().str.strip()
            df[col] = df[col].replace(null_values, np.nan)
        
        return df
    except Exception as e:
        return df

def fix_date(df):
    try:
        date_col = df.columns[df.columns.str.contains( "date|time|dob|created|updated|timestamp", case=False)]
        df[date_col] = df[date_col].apply(pd.to_datetime, format="mixed", errors="coerce")
        return df
    except Exception as e:
        return df

def fix_email(df):
    email_col = []
    incomplete_records = pd.DataFrame()
    duplicate_records = pd.DataFrame()
    try:
        email_pattern = r'^[a-zA-Z0-9]+([._%+-][a-zA-Z0-9]+)*@[a-zA-Z0-9-]+(\.[a-zA-Z]{2,})+$'
        df_col = df.select_dtypes(include=["object", "string"])
        for col in df_col:
            data = df[col].dropna().astype(str).str.match(email_pattern, case=False).mean()
            if data > 0.8:
                email_col.append(col)
        if not email_col:
            return df, incomplete_records, duplicate_records
        clean_df = df.copy()
        incomplete_records = clean_df[clean_df[email_col].isna().any(axis=1)].copy()
        clean_df.dropna(subset=email_col, how="any", inplace=True)
        duplicate_mask = clean_df[email_col].duplicated(keep=False)
        duplicate_records = clean_df[duplicate_mask].copy()
        clean_df.drop_duplicates(subset=email_col, keep="first", inplace=True)
        return clean_df, incomplete_records, duplicate_records
        
    except Exception as e:
        return df, incomplete_records, duplicate_records
    
def fix_id(df):
    id_col = []
    incomplete_records = pd.DataFrame()
    duplicate_records = pd.DataFrame()
    try:
        if df.empty:
            return df, incomplete_records, duplicate_records

        id_pattern =r'(id|uuid|guid|sno|serial|key)'
        target_Col = df.columns[df.columns.str.contains(id_pattern, case=False, regex=True)]
        for col in target_Col:
            non_null = df[col].notna().sum()
            if non_null == 0:
                continue
            unique = df[col].nunique(dropna=True)
            unique_ratio = unique / non_null

            # if unique_ratio > 0.7 and unique > 10:
            id_col.append(col)
            
        if not id_col:
            return df, incomplete_records, duplicate_records
        new_df = df.copy()
        for col in id_col:
            new_df[col] = pd.to_numeric(new_df[col], errors="coerce").astype("Int64")
        incomplete_records = new_df[new_df[id_col].isna().any(axis=1)].copy()
        new_df.dropna(subset=id_col, how="any", inplace=True)
        duplicate_records = new_df[new_df[id_col].duplicated(keep=False)].copy()
        new_df.drop_duplicates(subset=id_col, keep="first", inplace=True)
        return new_df, incomplete_records, duplicate_records
    except Exception as e:
        return new_df, incomplete_records, duplicate_records

def clean(x):
    if pd.isna(x):
        return x
    x = str(x).lower().strip()
    is_k = bool(re.search(r"\d+(\.\d+)?\s*k\b", x))
    is_m = bool(re.search(r"\d+(\.\d+)?\s*m\b", x))
    x_clean = re.sub(r"₹\.?|rs\.?|inr|,|\$", "", x)
    try:
        word = w2n.word_to_num(x_clean)
        return word
    except:
        pass
    x_clean = re.sub(r"[^\d.]", "", x)
    if is_k or is_m:
        match = re.search(r"\d+(\.\d+)?", x_clean)
        if match:
            num = float(match.group())
            if is_k:
                return num * 1000
            elif is_m:
                return num * 1000000
    try:
        return float(x_clean)
    except:
        return x

def numeric_convert(df):
    ob_col = df.select_dtypes(include=["object", "string"]).columns
    for col in ob_col:
        s = df[col].apply(clean)
        target = pd.to_numeric(s, errors="coerce")
        unique_ratio = s.nunique(dropna=True) / len(s)
        valid_ratio = target.notna().mean()
        if valid_ratio > 0.7 and unique_ratio < 0.9:
            df[col] = target

    return df

def smart_fill(df):
    df = df.copy()
    if df.empty:
        return df, pd.DataFrame()
    fill_log = []
    num_col = df.select_dtypes(include="number").columns
    for col in num_col:
        before = df[col].isna().sum()
        median = df[col].median()
        if pd.notna(median):
            df[col] = df[col].fillna(median)
        after = df[col].isna().sum()
        if before > after:
            fill_log.append({"column":col,
                            "method":"median",
                            "filled_values":before - after})
            
    date_col = df.select_dtypes(include=["datetime64[ns]"]).columns
    for col in date_col:
        before = df[col].isna().sum()
        df[col] = df[col].ffill()
        after = df[col].isna().sum()
        if before > after:
            fill_log.append({"column":col,
                            "method":"ffill",
                            "filled_values":before - after})

    object_col = df.select_dtypes(include=["string", "object"]).columns
    for col in object_col:
        before = df[col].isna().sum()
        null_ratio = before / len(df)
        if null_ratio > 0.4:
            df[col] = df[col].fillna("missing")
            method = "missing_high_null"
        else:
            mode = df[col].mode()
            if not mode.empty:
                df[col] = df[col].fillna(mode[0])
                method = "mode"
            else:
                method = None
        after = df[col].isna().sum()
        if before > after:
            fill_log.append({"column":col,
                            "method":method,
                            "filled_values":before - after})
        
    fill_df = pd.DataFrame(fill_log)
    return df, fill_df
    
def fun_col(df):
    new_df = df.copy()
    if len(new_df) == 0:
        empty =  pd.DataFrame()
        return new_df, empty, empty
    new_df.dropna(how="all", inplace=True)
    new_df.dropna(axis=1, how="all", inplace=True)
    new_df = strip_lower(new_df)
    new_df = fix_date(new_df)
    new_df, email_incomplete, email_duplicate = fix_email(new_df)
    new_df, id_incomplete, id_duplicate = fix_id(new_df)
    incomplete_records = pd.concat([email_incomplete, id_incomplete], ignore_index=True)
    duplicate_records = pd.concat([email_duplicate, id_duplicate], ignore_index=True)
    new_df  = numeric_convert(new_df)
    summary = {
        "Total_row": df.shape[0],
        "Total_columns":df.shape[1],
        "clean_rows":new_df.shape[0],
        "clean_columns":new_df.shape[1]
    }
    return new_df, incomplete_records, duplicate_records, summary

def get_data():
    try:
        print("=== Data Cleaning Tool ===")
        print("Select input source:")
        print("1. CSV\n2. Excel\n3. MySQL")

        choice = input("Enter choice: ").strip().lower()
        if choice in ["1", "csv"]:
            file = input("Enter you file: ")
            return read_csv(file)
        elif choice in ["2", "excel"]:
            file =  input("Enter you file: ")
            return read_excel(file)
        elif choice in ["3", "mysql"]:
            return read_sql()
        else:
            print("invalid choice")
            return None
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def main():
    df = get_data()
    if df is not None:
        print(f"data loaded. shape: {df.shape}")
        df, incomplete_records, duplicate_records, summary = fun_col(df)

        for k, v in summary.items():
            print(f"{k} = ({v})")

        print(f"data priview\n{df.head(5)}")
        choice = input("\nFill missing values? (yes/no):").strip().lower()
        if "y" in choice:
            clean_df, fill_log = smart_fill(df)
        else:
            clean_df = df
            fill_log = pd.DataFrame()
        output_file = "clean_data.xlsx"
        with pd.ExcelWriter("clean_data.xlsx") as writer:
            clean_df.to_excel(writer, sheet_name="clean_data", index=False)
            incomplete_records.to_excel(writer, sheet_name="incomplete_records", index=False)
            duplicate_records.to_excel(writer, sheet_name="duplicate_records", index=False)
            if not fill_log.empty:
                fill_log.to_excel(writer, sheet_name="fill_log", index=False)

        print(f"\nData saved successfully to '{output_file}'")

if __name__ == "__main__":
    main()
