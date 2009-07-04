-- Combination of the most important inflection related information for words.

DROP VIEW view_voikko_inflection;

CREATE VIEW view_voikko_inflection AS
SELECT w.wid, w.word, coalesce(rword.related_word, w.word) AS wstruct,
  inf.value AS infclass,
  CASE WHEN frontv.aid IS NULL THEN false ELSE true END AS frontv,
  CASE WHEN backv.aid IS NULL THEN false ELSE true END AS backv,
  CASE WHEN noplural.aid IS NULL THEN false ELSE true END AS noplural
FROM word w
LEFT JOIN related_word rword ON w.wid = rword.wid
  AND replace(replace(rword.related_word, '=', ''), '|', '') = w.word
LEFT JOIN string_attribute_value inf ON w.wid = inf.wid AND inf.aid = 1
LEFT JOIN flag_attribute_value frontv ON w.wid = frontv.wid AND frontv.aid = 22
LEFT JOIN flag_attribute_value backv ON w.wid = backv.wid AND backv.aid = 23
LEFT JOIN flag_attribute_value noplural ON w.wid = noplural.wid AND noplural.aid = 37
WHERE w.wid NOT IN (SELECT a.wid FROM flag_attribute_value a WHERE a.aid IN (5, 24, 26));

COMMENT ON VIEW view_voikko_inflection IS 'Inflection information for words in Voikko';
COMMENT ON COLUMN view_voikko_inflection.wid IS 'Word id';
COMMENT ON COLUMN view_voikko_inflection.word IS 'Base form';
COMMENT ON COLUMN view_voikko_inflection.wstruct IS 'Word structure pattern';
COMMENT ON COLUMN view_voikko_inflection.infclass IS 'Inflection class';
COMMENT ON COLUMN view_voikko_inflection.frontv IS 'Vowel harmony (front)';
COMMENT ON COLUMN view_voikko_inflection.backv IS 'Vowel harmony (back)';
COMMENT ON COLUMN view_voikko_inflection.noplural IS 'No plural forms for this word';

GRANT SELECT ON view_voikko_inflection TO joukahainen;
