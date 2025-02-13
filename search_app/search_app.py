from flask import Flask, render_template, request
import requests
import pandas as pd
import io
#from app import app

app = Flask(__name__)

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

def apply_soundex_filter(df, column, term):
    soundex_term = soundex(term)
    return df[df[column].apply(lambda x: soundex(x) == soundex_term)]

def soundex(name):
    name = name.upper()
    soundex = ""
    soundex += name[0]
    dictionary = {"BFPV": "1", "CGJKQSXZ": "2", "DT": "3", \
                  "L": "4", "MN": "5", "R": "6", "AEIOUHWY": "."}
    for char in name[1:]:
        for key in dictionary.keys():
            if char in key:
                code = dictionary[key]
                if code != soundex[-1]:
                    soundex += code
    soundex = soundex.replace(".", "")
    soundex = soundex[:4].ljust(4, "0")
    return soundex

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("search_app-page.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    df = fetch_csv_data()
#    columns = ["FirstNameNorm", "LastNameNorm", "TownOfOrigin", "Notes", "Year"]
    field_mapping = {
        "Given Name": "FirstNameNorm",
        "Surname": "LastNameNorm",
        "Town": "TownOfOrigin",
        "Comments": "Notes",
        "Year": "Year"
    }
    filtered_data = df[df["WitnessInd"] == False] if request.form.get("witness-ind") == "on" else df

    if request.method == "POST":
        for field in ["Given Name", "Surname", "Town", "Comments", "Year"]:
            search_term = request.form.get(f"search-input-{field.replace(' ', '-').lower()}")
            if search_term:
                column = field_mapping[field]
                if field in ["Given Name", "Surname", "Town"]:
                    if "%" in search_term or "_" in search_term:
                        sql_wildcards = search_term.replace("%", ".*").replace("_", ".")
                        filtered_data = filtered_data[filtered_data[column] \
                            .str.contains(sql_wildcards, na=False, regex=True)][["EntryNum"]] \
                            .drop_duplicates(subset=["EntryNum"], keep='first') \
                            .merge(filtered_data, on='EntryNum', validate="1:m")
                    else:
                        filtered_data = apply_soundex_filter(filtered_data, column, search_term)[["EntryNum"]] \
                            .drop_duplicates(subset=["EntryNum"], keep='first') \
                            .merge(filtered_data, on='EntryNum', validate="1:m")
                else:
                    filtered_data = filtered_data[filtered_data[column] \
                        .str.contains(search_term, na=False, case=False)][["EntryNum"]] \
                        .drop_duplicates(subset=["EntryNum"], keep='first') \
                        .merge(filtered_data, on='EntryNum', validate="1:m")

    return render_template("search_app-results.html", columns=filtered_data.columns, data=filtered_data)

if __name__ == "__main__":
    app.run(debug=True)
