-- Static database data for Joukahainen/Hunspell-fi (public data)

\c joukahainen

-- Delete old data
DELETE FROM related_word;
DELETE FROM flag_attribute_value;
DELETE FROM string_attribute_value;
DELETE FROM event;
DELETE FROM task_word;
DELETE FROM task;
DELETE FROM word;
DELETE FROM attribute_class;
DELETE FROM attribute;
DELETE FROM attribute_type;
DELETE FROM wordclass;
DELETE FROM language;
DELETE FROM appuser;

-- Insert new data
INSERT INTO language(langid, name) VALUES(1, 'suomi');
INSERT INTO wordclass(classid, name) VALUES(1, 'substantiivi');
INSERT INTO wordclass(classid, name) VALUES(2, 'adjektiivi');
INSERT INTO wordclass(classid, name) VALUES(3, 'verbi');
INSERT INTO attribute_type(type, descr) VALUES(1, 'string');
INSERT INTO attribute_type(type, descr) VALUES(2, 'flag');
INSERT INTO attribute(aid, descr, type, editable) VALUES(1, 'taivutusluokka', 1, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(1, 1);
INSERT INTO attribute_class(aid, classid) VALUES(1, 2);
INSERT INTO attribute_class(aid, classid) VALUES(1, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(2, 'ala: puhekieltä tai murretta', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(2, 1);
INSERT INTO attribute_class(aid, classid) VALUES(2, 2);
INSERT INTO attribute_class(aid, classid) VALUES(2, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(3, 'inen-johdin aina sallittu', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(3, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(4, 'inen-johdin ei koskaan sallittu', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(4, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(5, 'ei kuulu oikolukusanastoon', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(5, 1);
INSERT INTO attribute_class(aid, classid) VALUES(5, 2);
INSERT INTO attribute_class(aid, classid) VALUES(5, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(6, 'ei kuulu indeksointisanastoon', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(6, 1);
INSERT INTO attribute_class(aid, classid) VALUES(6, 2);
INSERT INTO attribute_class(aid, classid) VALUES(6, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(7, 'ei sallittu yhdyssanan osana', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(7, 1);
INSERT INTO attribute_class(aid, classid) VALUES(7, 2);
INSERT INTO attribute(aid, descr, type, editable) VALUES(8, 'ei sallittu yhdyssanan alkuosana', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(8, 1);
INSERT INTO attribute_class(aid, classid) VALUES(8, 2);
INSERT INTO attribute(aid, descr, type, editable) VALUES(9, 'ei sallittu yhdyssanan jälkiosana', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(9, 1);
INSERT INTO attribute_class(aid, classid) VALUES(9, 2);
INSERT INTO attribute(aid, descr, type, editable) VALUES(10, 'sana on myös substantiivi', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(10, 2);
INSERT INTO attribute(aid, descr, type, editable) VALUES(11, 'erisnimi: etunimi', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(11, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(12, 'erisnimi: sukunimi', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(12, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(13, 'erisnimi: paikannimi', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(13, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(14, 'erisnimi: luokittelematon erisnimi', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(14, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(15, 'ala: atk', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(15, 1);
INSERT INTO attribute_class(aid, classid) VALUES(15, 2);
INSERT INTO attribute_class(aid, classid) VALUES(15, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(16, 'historiallinen taivutusluokka', 1, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(16, 1);
INSERT INTO attribute_class(aid, classid) VALUES(16, 2);
INSERT INTO attribute_class(aid, classid) VALUES(16, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(17, 'ala: sivistyssana', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(17, 1);
INSERT INTO attribute_class(aid, classid) VALUES(17, 2);
INSERT INTO attribute_class(aid, classid) VALUES(17, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(18, 'lyhyt sanan selitys', 1, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(18, 1);
INSERT INTO attribute_class(aid, classid) VALUES(18, 2);
INSERT INTO attribute_class(aid, classid) VALUES(18, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(19, 'ala: kasvatustiede', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(19, 1);
INSERT INTO attribute_class(aid, classid) VALUES(19, 2);
INSERT INTO attribute_class(aid, classid) VALUES(19, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(20, 'paikannimi: taipuu sisäpaikallissijoissa', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(20, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(21, 'paikannimi: taipuu ulkopaikallissijoissa', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(21, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(22, 'vokaalisointu: etuvokaalipäätteet (yäö)', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(22, 1);
INSERT INTO attribute_class(aid, classid) VALUES(22, 2);
INSERT INTO attribute_class(aid, classid) VALUES(22, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(23, 'vokaalisointu: takavokaalipäätteet (uao)', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(23, 1);
INSERT INTO attribute_class(aid, classid) VALUES(23, 2);
INSERT INTO attribute_class(aid, classid) VALUES(23, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(24, 'virheellinen sana', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(24, 1);
INSERT INTO attribute_class(aid, classid) VALUES(24, 2);
INSERT INTO attribute_class(aid, classid) VALUES(24, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(25, 'vaatii selvennystä', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(25, 1);
INSERT INTO attribute_class(aid, classid) VALUES(25, 2);
INSERT INTO attribute_class(aid, classid) VALUES(25, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(26, 'siirretty', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(26, 1);
INSERT INTO attribute_class(aid, classid) VALUES(26, 2);
INSERT INTO attribute_class(aid, classid) VALUES(26, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(27, 'ei lAinen -johdosta', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(27, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(28, 'fi.wiktionary.org', 1, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(28, 1);
INSERT INTO attribute_class(aid, classid) VALUES(28, 2);
INSERT INTO attribute_class(aid, classid) VALUES(28, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(29, 'vain yhdyssanan jälkiosana', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(29, 1);
INSERT INTO attribute_class(aid, classid) VALUES(29, 2);
INSERT INTO attribute_class(aid, classid) VALUES(29, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(30, 'ei mAinen -johdosta', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(30, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(31, 'yksitekijäinen teonsana', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(31, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(32, 'ei taivu vertailumuodoissa', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(32, 2);

INSERT INTO appuser(uid, uname) VALUES(1, 'malagaconverter');
-- Test user, password 'testi'
INSERT INTO appuser(uid, uname, firstname, lastname) VALUES(2, 'testi', 'Aku', 'Ankka');

INSERT INTO task(tid, descr, sql, orderby) VALUES(1, 'Substantiivien taivutusluokkien tarkistus',
  'SELECT taskw.wid, tasksa.value AS tluokka FROM word taskw, string_attribute_value tasksa WHERE taskw.class = 1 AND tasksa.aid = 1 AND tasksa.wid = taskw.wid',
  't.tluokka, w.word');
INSERT INTO task(tid, descr, sql, orderby) VALUES(2, 'Adjektiivien taivutusluokkien tarkistus',
  'SELECT taskw.wid, tasksa.value AS tluokka FROM word taskw, string_attribute_value tasksa WHERE taskw.class = 2 AND tasksa.aid = 1 AND tasksa.wid = taskw.wid',
  't.tluokka, w.word');
INSERT INTO task(tid, descr, sql, orderby) VALUES(3, 'Verbien taivutusluokkien tarkistus',
  'SELECT taskw.wid, tasksa.value AS tluokka FROM word taskw, string_attribute_value tasksa WHERE taskw.class = 3 AND tasksa.aid = 1 AND tasksa.wid = taskw.wid',
  't.tluokka, w.word');

\c joukahainen_private
DELETE FROM appuser;
INSERT INTO appuser(uid, uname, firstname, lastname, pwhash)
  VALUES(2, 'testi', 'Aku', 'Ankka', 'f4f1017a0a37f7772e50d98d2ca58fc9533c03b0');
