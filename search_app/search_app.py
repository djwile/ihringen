from flask import Flask, render_template, request
import requests
import pandas as pd
import io
from itertools import groupby
from operator import itemgetter
#from datetime import datetime
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


def get_month_value(date_str):
    """Convert the first 3 characters of date string to month number"""
    if not isinstance(date_str, str):
        return 13  # Put None/NaN values at the end

    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    try:
        return month_map.get(date_str[:3], 13)
    except:
        return 13


def get_event_order(event):
    """Define custom event ordering"""
    event_order = {
        'Birth': 1,
        'Bris': 2,
        'Adoption': 3,
        'Legitimation': 4,
        'Wedding': 5,
        'Death': 6,
        'Burial': 7
    }
    if not isinstance(event, str):
        return 999  # Put None/NaN values at the end
    return event_order.get(event, ord('z') - ord(event[0]) if event else 999)


def get_relationship_order(relationship):
    """Define custom relationship ordering"""
    relationship_order = {
        'Child': 1,
        'Death': 2,
        'Husband': 3,
        'Wife': 4,
        'First wife': 5,
        'Second wife': 6,
        'First husband': 7,
        'Father': 8,
        'Mother': 9,
        "Father's father": 10,
        "Mother's father": 11,
        "Mother's mother": 12,
        "Husband's father": 13,
        "Husband's mother": 14,
        "Wife's father": 15,
        "Wife's mother": 16,
        "Wife's first husband": 17,
        'Witness': 18
    }
    if not isinstance(relationship, str):
        return 999  # Put None/NaN values at the end
    return relationship_order.get(relationship, ord('z') - ord(relationship[0]) if relationship else 999)


@application.route("/", methods=["GET", "POST"])
def index():
    return render_template("search_app-page.html")

@application.route("/search", methods=["GET", "POST"])
def search():
    df = fetch_csv_data()
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


    # Define the columns that should span rows when values are identical
    SPANNING_COLUMNS = ['EntryNum','Year', 'Date', 'Event', 'Permalink']

    if filtered_data is not None and not filtered_data.empty:
        # Create sorting helper columns
        filtered_data['_month_order'] = filtered_data['Date'].apply(get_month_value)
        filtered_data['_event_order'] = filtered_data['Event'].apply(get_event_order)
        filtered_data['_relationship_order'] = filtered_data['Relationship'].apply(get_relationship_order)

        # Sort the data using our custom ordering
        filtered_data = filtered_data.sort_values(
            by=[
                'EntryNum',
                'Year',
                '_month_order',
                '_event_order',
                '_relationship_order'
            ],
            ascending=[True, True, True, True, True],
            key=lambda x: pd.Series(x).apply(lambda y: pd.to_numeric(y) if pd.notna(y) else pd.NA)
        )

        # Drop helper columns
        filtered_data = filtered_data.drop(columns=['_month_order', '_event_order', '_relationship_order'])

        # Convert to list of dicts for easier handling in template
        data_list = filtered_data.to_dict('records')

        # Group the data by EntryNum
        grouped_data = []
        for key, group in groupby(data_list, key=itemgetter('EntryNum')):
            group_list = list(group)

           # Calculate row spans for specified columns within this EntryNum group
            group_spans = {}

            # Handle EntryNum first - it always spans the entire group
            group_spans['EntryNum'] = [len(group_list)] + [0] * (len(group_list) - 1)

            # For each other column that we want to check for spans
            for column in SPANNING_COLUMNS[1:]:  # Skip EntryNum as we handled it above
                if column in filtered_data.columns:
                    spans = [0] * len(group_list)  # Initialize all spans to 0
                    i = 0
                    while i < len(group_list):
                        if spans[i] == 0:  # Only process positions that haven't been spanned yet
                            # Count how many subsequent rows have the same value
                            span_count = 1
                            current_value = group_list[i][column]
                            j = i + 1
                            while j < len(group_list) and group_list[j][column] == current_value:
                                span_count += 1
                                j += 1

                            # Set the span count at the start of the span
                            if span_count > 1:
                                spans[i] = span_count
                                # Mark subsequent positions as part of this span
                                for k in range(i + 1, i + span_count):
                                    spans[k] = 0
                            else:
                                spans[i] = 1

                            i = j  # Skip to end of current span
                        else:
                            i += 1

                    group_spans[column] = spans

            # Add the spans information to each row
            for i, row in enumerate(group_list):
                row['_spans'] = {col: group_spans[col][i] for col in group_spans}

            grouped_data.append(group_list)

    else:
        grouped_data = []

    return render_template("search_app-results.html",
                         columns=filtered_data.columns if filtered_data is not None else [],
                         grouped_data=grouped_data,
                         spanning_columns=SPANNING_COLUMNS)

if __name__ == "__main__":
    application.run(debug=True)
