-- Static database data for Joukahainen/Hunspell-fi

-- Delete old data
DELETE FROM attribute_class;
DELETE FROM attribute;
DELETE FROM wordclass;
DELETE FROM language;

-- Insert new data
INSERT INTO language(langid, name)
       VALUES(1, 'suomi');
INSERT INTO wordclass(classid, name)
       VALUES(1, 'substantiivi');
INSERT INTO attribute(aid, name, type, editable)
       VALUES(1, 'taivutusluokka', 1, TRUE);
INSERT INTO attribute_class(aid, classid)
       VALUES(1, 1);

