-- Static database data for Joukahainen/Hunspell-fi

-- Delete old data
DELETE FROM related_word;
DELETE FROM flag_attribute_value;
DELETE FROM string_attribute_value;
DELETE FROM word;
DELETE FROM attribute_class;
DELETE FROM attribute;
DELETE FROM attribute_type;
DELETE FROM wordclass;
DELETE FROM language;

-- Insert new data
INSERT INTO language(langid, name) VALUES(1, 'suomi');
INSERT INTO wordclass(classid, name) VALUES(1, 'substantiivi');
INSERT INTO wordclass(classid, name) VALUES(2, 'adjektiivi');
INSERT INTO attribute_type(type, descr) VALUES(1, 'string');
INSERT INTO attribute_type(type, descr) VALUES(2, 'flag');
INSERT INTO attribute(aid, descr, type, editable) VALUES(1, 'taivutusluokka', 1, TRUE);
INSERT INTO attribute(aid, descr, type, editable) VALUES(2, 'puhekieltä tai murretta', 2, TRUE);
INSERT INTO attribute(aid, descr, type, editable) VALUES(3, 'inen-johdin aina sallittu', 2, TRUE);
INSERT INTO attribute(aid, descr, type, editable) VALUES(4, 'inen-johdin ei koskaan sallittu', 2, TRUE);
INSERT INTO attribute(aid, descr, type, editable) VALUES(5, 'ei kuulu oikolukusanastoon', 2, TRUE);
INSERT INTO attribute(aid, descr, type, editable) VALUES(6, 'ei kuulu indeksointisanastoon', 2, TRUE);
INSERT INTO attribute(aid, descr, type, editable) VALUES(7, 'ei sallittu yhdyssanan osana', 2, TRUE);
INSERT INTO attribute(aid, descr, type, editable) VALUES(8, 'ei sallittu yhdyssanan alkuosana', 2, TRUE);
INSERT INTO attribute(aid, descr, type, editable) VALUES(9, 'ei sallittu yhdyssanan jälkiosana', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(1, 1);

