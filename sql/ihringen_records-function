# Creates a function which returns the more useful columns for all rows pertaining to any Entry which contains the
# Surname and Given Name arguments provided (SQL wildcards can be used as well). Trivial to adjust inputs to allow 
# for more specific identifiers like PersonID as well.

CREATE OR REPLACE FUNCTION ihringen_records(surname VARCHAR, givenname VARCHAR) 
	RETURNS TABLE (
		EntryNum INTEGER,
		Standesbuch VARCHAR(9),
		Bild INTEGER,
		Year INTEGER,
		Date VARCHAR(6),
		"time" TIME WITHOUT TIME ZONE,
		Event VARCHAR(32),
		Sex VARCHAR(1),
		PrimaryInd BOOLEAN,
		Relationship VARCHAR(32),
		FirstNameNorm VARCHAR(32),
		LastNameNorm VARCHAR(32),
		TownOfOrigin VARCHAR(64),
		Age VARCHAR(64),
		Status VARCHAR(128),
		Occupation VARCHAR(128),
		Notes VARCHAR,
		PersonID VARCHAR(7),
		BirthXRef INTEGER,
		MarriageXRef INTEGER,
		DeathXRef INTEGER,
		OtherXRef INTEGER,
		OtherXRefEvent VARCHAR(32),
		NonJewInd BOOLEAN,
		DeadInd BOOLEAN,
		Permalink VARCHAR(60)
	)
AS $BODY$
BEGIN 
	RETURN QUERY
WITH entrynums AS (
	SELECT DISTINCT i.EntryNum
	FROM ihringen.ihringen_data_main i
		WHERE i.LastNameNorm ILIKE surname
		AND i.FirstNameNorm ILIKE givenname
)
SELECT 
		e.EntryNum,
		i.Standesbuch,
		i.Bild,
		i.Year,
		i.Date,
		i.Time,
		i.Event,
		i.Sex,
		i.PrimaryInd,
		i.Relationship,
		i.FirstNameNorm,
		i.LastNameNorm,
		i.TownOfOrigin,
		i.Age,
		i.Status,
		i.Occupation,
		i.Notes,
		i.PersonID,
		i.BirthXRef,
		i.MarriageXRef,
		i.DeathXRef,
		i.OtherXRef,
		i.OtherXRefEvent,
		i.NonJewInd,
		i.DeadInd,
		i.Permalink
FROM entrynums e
INNER JOIN ihringen.ihringen_data_main i
ON e.EntryNum = i.EntryNum
; 
END; $BODY$

LANGUAGE 'plpgsql';
