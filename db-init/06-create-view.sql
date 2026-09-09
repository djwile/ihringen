CREATE OR REPLACE VIEW ihringen.ihringen_data_main
AS
SELECT entrynum,
    standesbuch,
    bild,
    year,
    date,
    "time",
    event,
    sex,
    primaryind,
    secondaryind,
    witnessind,
    relationship,
    firstnamenorm,
    firstnamecert,
    lastnamenorm,
    lastnamecert,
    townoforigin,
    towncertainty,
    age,
    jungaltind,
    illegitind,
    status,
    occupation,
    notes,
    personid,
    birthxref,
    marriagexref,
    deathxref,
    otherxref,
    otherxrefevent,
    nonjewind,
    deadind,
    firstnamexct,
    lastnamexct,
    mistakennameind,
    permalink
FROM ihringen.ihringen_data
WHERE witnessind = false;

ALTER TABLE ihringen.ihringen_data_main
    OWNER TO ihringen;
