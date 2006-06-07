-- Static database data for Joukahainen/Hunspell-fi

-- Delete old data
DELETE FROM attribute_class;
DELETE FROM attribute;
DELETE FROM attribute_type;
DELETE FROM wordclass;
DELETE FROM language;

-- Insert new data
INSERT INTO language(langid, name) VALUES(1, 'suomi');
INSERT INTO wordclass(classid, name) VALUES(1, 'substantiivi');
INSERT INTO attribute_type(type, descr) VALUES(1, 'string');
INSERT INTO attribute_type(type, descr) VALUES(2, 'flag');
INSERT INTO attribute(aid, descr, type, editable) VALUES(1, 'taivutusluokka', 1, TRUE);
INSERT INTO attribute(aid, descr, type, editable) VALUES(2, 'puhekieltä tai murretta', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(1, 1);

