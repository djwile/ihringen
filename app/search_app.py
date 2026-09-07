from flask import Flask, render_template, request
import psycopg2
import os
import pandas as pd
from itertools import groupby
from operator import itemgetter
from .packages.phonetik import koelner_phonetik, apply_phonetic_filter

# from packages.phonetik import koelner_phonetik, apply_phonetic_filter

application = Flask(__name__)

"""
CSV_URL = "https://api.github.com/repos/djwile/ihringen/contents/data/ihringen_database-csv.csv?ref=main"

def fetch_data():
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    response = requests.get(CSV_URL, headers=headers)
    csv_data = response.content.decode('utf-8')
    df = pd.read_csv(io.StringIO(csv_data))
    return df
"""

def fetch_data():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("SELECT * FROM ihringen.ihringen")
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns = colnames)
    cur.close()
    conn.close()

    return df

# Unable to import phonetik module, uncomment to run
"""
def koelner_phonetik(name):
"""    
    """
    Implements the Kölner Phonetik (Cologne Phonetics) algorithm for German phonetic matching.
    Adapted for historical German-Jewish names from the 19th century.
    
    Rules based on: https://de.wikipedia.org/wiki/Kölner_Phonetik
    """ 
"""
    if not name:
        return "0000"
        
    # Convert to uppercase and split compound names
    name_parts = name.upper().split()
    result_codes = []
    
    for part in name_parts:
        # Initial preprocessing
        word = part.replace('Ä', 'AE').replace('Ö', 'OE').replace('Ü', 'UE')
        word = word.replace('ß', 'SS').replace('É', 'E').replace('È', 'E')
        
        if not word:
            continue
            
        code = []
        last_code = -1  # Initialize with invalid code
        length = len(word)
        
        # Process each character
        for i in range(length):
            c = word[i]
            
            # Rules for specific positions and combinations
            if c in 'AEIJOUYHW':
                current_code = 0
            elif c in 'B':
                current_code = 1
            elif c in 'P':
                if i + 1 < length and word[i + 1] == 'H':
                    current_code = 3
                else:
                    current_code = 1
            elif c in 'DT':
                if i + 1 < length and word[i + 1] in 'CSZ':
                    current_code = 8
                else:
                    current_code = 2
            elif c in 'F':
                current_code = 3
            elif c in 'GKQ':
                current_code = 4
            elif c == 'C':
                if i == 0:
                    if i + 1 < length and word[i + 1] in 'AHKLOQRUX':
                        current_code = 4
                    else:
                        current_code = 8
                else:
                    if i > 0 and word[i - 1] in 'SZ':
                        current_code = 8
                    elif i + 1 < length and word[i + 1] in 'AHKOQUX':
                        current_code = 4
                    else:
                        current_code = 8
            elif c in 'X':
                if i == 0:
                    current_code = 48
                else:
                    current_code = 8
            elif c in 'L':
                current_code = 5
            elif c in 'MN':
                current_code = 6
            elif c in 'R':
                current_code = 7
            elif c in 'SZ':
                current_code = 8
            else:
                current_code = -1
                
            # Only append if code is different from last code
            if current_code != -1 and current_code != last_code:
                code.append(str(current_code))
                last_code = current_code
        
        # Remove zeros except at start
        if code:
            result = code[0] + ''.join(c for c in code[1:] if c != '0')
            # Pad with zeros to make it 4 characters
            result = (result + '0' * 4)[:4]
            result_codes.append(result)
    
    return ' '.join(result_codes) if result_codes else '0000'

def apply_phonetic_filter(df, column, term):
    """
    Applies Kölner Phonetik filtering to a DataFrame column.
    Handles compound names by matching each part independently.
    """
    name_parts_phonetic = koelner_phonetik(term).split()
    
    # Create a mask for each part of the name
    mask = pd.Series([True] * len(df), index=df.index)
    for i, part_phonetic in enumerate(name_parts_phonetic):
        part_mask = df[column].apply(lambda x: 
            len(koelner_phonetik(x).split()) > i and 
            koelner_phonetik(x).split()[i] == part_phonetic)
        mask = mask & part_mask
    
    return df[mask]
"""


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


def get_standesbuch_order(standesbuch):
    """Give ordinal numbers to Standesbuecher"""
    standesbuch_order = {
        '1811-1820': 1,
        '1821-1828': 2,
        '1829-1834': 3,
        '1835-1840': 4,
        '1841-1845': 5,
        '1846-1851': 6,
        '1852-1858': 7,
        '1859-1864': 8,
        '1865-1870': 9
    }
    if not isinstance(standesbuch, str):
        return 999  # Put None/NaN values at the end
    return standesbuch_order.get(standesbuch, ord('z') - ord(standesbuch[0]) if standesbuch else 999)


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


def get_time_order(time):
    return time[:2]


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


@application.route("/about")
def about():
    return render_template("static_pages/about.html")


@application.route("/data-dictionary")
def data_dictionary():
    return render_template("static_pages/data_dictionary.html")


@application.route("/earlier-records")
def earlier_records():
    return render_template("static_pages/earlier_records.html")


@application.route("/contact")
def contact():
    return render_template("static_pages/contact.html")


@application.route("/search", methods=["GET", "POST"])
def search():
    df = fetch_data()
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
                        filtered_rows = filtered_rows[filtered_rows[column]\
                            .str.contains(sql_wildcards, na=False, regex=True)]
                    else:
                        filtered_rows = apply_phonetic_filter(filtered_rows, column, search_term)
                elif field in ["Entry", "Person ID", "Year"]:
                    filtered_rows = filtered_rows[filtered_rows[column] \
                         .str.match(search_term, na=False, case=False)]
                else:
                     filtered_rows = filtered_rows[filtered_rows[column] \
                         .str.contains(search_term, na=False, case=False)]

        filtered_data = filtered_rows[["EntryNum"]] \
            .drop_duplicates(subset=["EntryNum"], keep='first') \
            .merge(filtered_data, on='EntryNum', validate="1:m")


    # Define the columns that should span rows when values are identical
    SPANNING_COLUMNS = ['EntryNum', 'Standesbuch', 'Year', 'Bild', 'Date', 'Event', 'Time', 'Permalink']

    if filtered_data is not None and not filtered_data.empty:
        # Create sorting helper columns
        filtered_data['_month_order'] = filtered_data['Date'].apply(get_month_value)
        filtered_data['_event_order'] = filtered_data['Event'].apply(get_event_order)
        filtered_data['_relationship_order'] = filtered_data['Relationship'].apply(get_relationship_order)

        if request.form.get("abridged-data") == "on":
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
        else:
            filtered_data['_standesbuch_order'] = filtered_data['Standesbuch'].apply(get_standesbuch_order)
            filtered_data['_time_order'] = filtered_data['Time'].apply(get_time_order)
            filtered_data = filtered_data.sort_values(
                by=[
                    'EntryNum',
                    '_standesbuch_order',
                    'Year',
                    'Bild',
                    '_month_order',
                    '_event_order',
                    '_time_order',
                    '_relationship_order'
                ],
                ascending=[True, True, True, True, True, True, True, True],
                key=lambda x: pd.Series(x).apply(lambda y: pd.to_numeric(y) if pd.notna(y) else pd.NA)
            )

        # Drop helper columns
        if request.form.get("abridged-data") == "on":
            filtered_data = filtered_data.drop(columns=['_month_order', '_event_order', '_relationship_order'])
        else:
            filtered_data = filtered_data.drop(columns=['_standesbuch_order','_month_order','_event_order','_time_order','_relationship_order'])

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