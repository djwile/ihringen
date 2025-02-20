from flask import Flask, render_template, request
import requests
import pandas as pd
import io
#from app import app

application = Flask(__name__)

CSV_URL = "https://api.github.com/repos/djwile/ihringen/contents/data/ihringen_database-csv.csv?ref=main"

def fetch_csv_data():
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "X-GitHub-Api-Version": "2022-11-28" 
    }
    response = requests.get(CSV_URL, headers=headers)
    csv_data = response.content.decode('utf-8')
    df = pd.read_csv(io.StringIO(csv_data))
    return df


def soundex(name):
    name = name.upper()
    soundex = ""
    soundex += name[0]
    dictionary = {"BFPV": "1", "CGJKQSXZß": "2", "DT": "3", \
                  "L": "4", "MN": "5", "R": "6", "AEIOUHWYÄÖÜ": "."}
    for char in name[1:]:
        for key in dictionary.keys():
            if char in key:
                code = dictionary[key]
                if code != soundex[-1]:
                    soundex += code
    soundex = soundex.replace(".", "")
    soundex = soundex[:4].ljust(4, "0")
    return soundex


def apply_soundex_filter(df, column, term):
    soundex_term = soundex(term)
    return df[df[column].apply(lambda x: soundex(x) == soundex_term)]


def number_to_string(df):
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    for col in num_cols:
        if df[col].dtype == 'float64':
             df[col] = df[col].astype('Int64')
        else: df
        df[col] = df[col].astype(str)
    return df


def na_fix(df, dtype, fill):
    na_cols = df.columns[df.isna().any(axis=0)].union(df.columns[df.eq("<NA>").any(axis=0)])
    for col in na_cols:
        df[col] = df[col].fillna(fill).astype(dtype)
        df[col] = df[col].replace("<NA>", fill)
    return df


@application.route("/", methods=["GET", "POST"])
def index():
    return render_template("search_app-page.html")

@application.route("/search", methods=["GET", "POST"])
def search():
    df = fetch_csv_data()
#    columns = ["FirstNameNorm", "LastNameNorm", "TownOfOrigin", "Notes", "Year"]
    field_mapping = {
        "Entry": "EntryNum",
        "Person ID": "PersonID",
        "Given Name": "FirstNameNorm",
        "Surname": "LastNameNorm",
        "Town": "TownOfOrigin",
        "Comments": "Notes",
        "Year": "Year"
    }
    
    df = number_to_string(df)
    df = na_fix(df, str, "")
    
    #change '0' back to False if using boolean instead of string
    filtered_data = df[df["WitnessInd"] == '0'] \
        if request.form.get("witness-ind") == "on" else df

    filtered_data = filtered_data[["EntryNum", "Year", "Date", "Event", "Sex", \
             "PrimaryInd", "Relationship", "PersonID", "FirstNameNorm", "LastNameNorm", \
             "TownOfOrigin", "Age", "Status", "Occupation", "Notes", \
             "BirthXRef", "MarriageXRef", "DeathXRef", "OtherXRef", "OtherXRefEvent", \
             "Permalink"]] if request.form.get("abridged-data") == "on" else filtered_data

    filtered_rows = filtered_data

    if request.method == "POST":
        for field in ["Entry", "Person ID", "Given Name", "Surname", "Town", "Comments", "Year"]:
            search_term = request.form.get(f"search-input-{field.replace(' ', '-').lower()}")
            if search_term:
                column = field_mapping.get(field)
                if field in ["Given Name", "Surname", "Town"]:
                    if "%" in search_term or "_" in search_term:
                        sql_wildcards = search_term.replace("%", ".*").replace("_", ".")
                        filtered_rows = filtered_rows[filtered_rows[column] \
                            .str.contains(sql_wildcards, na=False, regex=True)]
                    else:
                        filtered_rows = apply_soundex_filter(filtered_rows, column, search_term)
                if field in ["Entry", "Person ID", "Year"]:
                    filtered_rows = filtered_rows[filtered_rows[column] \
                         .str.match(search_term, na=False, case=False)]
                else:
                     filtered_rows = filtered_rows[filtered_rows[column] \
                         .str.contains(search_term, na=False, case=False)]

        filtered_data = filtered_rows[["EntryNum"]] \
            .drop_duplicates(subset=["EntryNum"], keep='first') \
            .merge(filtered_data, on='EntryNum', validate="1:m")

    return render_template("search_app-results.html", columns=filtered_data.columns, data=filtered_data)

if __name__ == "__main__":
    application.run(debug=True)
