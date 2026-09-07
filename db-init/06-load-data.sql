\connect ihirngen

\copy ihringen.ihringen_data
FROM '/data/ihringen_database-csv.csv'
WITH (FORMAT csv, HEADER true);