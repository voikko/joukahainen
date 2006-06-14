-- Sample dynamic data for testing purposes (Joukahainen/Hunspell-fi)

-- Delete old data
DELETE FROM related_word;
-- DELETE FROM flag_attribute_value;
-- DELETE FROM string_attribute_value;
-- DELETE FROM word;

-- Insert new data
-- INSERT INTO word(wid, word, class) VALUES(1, 'hevonen', 1);
-- INSERT INTO word(wid, word, class) VALUES(2, 'isi',     1);
-- INSERT INTO string_attribute_value(wid, aid, value) VALUES(1, 1, 'nainen');
-- INSERT INTO flag_attribute_value(wid, aid) VALUES(2, 2);

INSERT INTO related_word(wid, related_word) VALUES(
 (SELECT wid FROM word WHERE word='shamaani'), 'šamaani');
INSERT INTO related_word(wid, related_word) VALUES(
 (SELECT wid FROM word WHERE word='shamaani'), 'shamaani');
INSERT INTO related_word(wid, related_word) VALUES(
 (SELECT wid FROM word WHERE word='loppuunmyynti'), 'loppuun|myynti');
