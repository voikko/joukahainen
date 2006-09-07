-- Static database data for English installation of Joukahainen

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

-- Word classes and metadata fields
INSERT INTO wordclass(classid, name) VALUES(1, 'verb');
INSERT INTO wordclass(classid, name) VALUES(2, 'noun');
INSERT INTO wordclass(classid, name) VALUES(3, 'adjective');
INSERT INTO attribute_type(type, descr) VALUES(1, 'string');
INSERT INTO attribute_type(type, descr) VALUES(2, 'flag');
INSERT INTO attribute(aid, descr, type, editable) VALUES(1, 'short explanation', 1, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(1, 1);
INSERT INTO attribute_class(aid, classid) VALUES(1, 2);
INSERT INTO attribute_class(aid, classid) VALUES(1, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(2, 'incorrect word', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(2, 1);
INSERT INTO attribute_class(aid, classid) VALUES(2, 2);
INSERT INTO attribute_class(aid, classid) VALUES(2, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(3, 'should be checked', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(3, 1);
INSERT INTO attribute_class(aid, classid) VALUES(3, 2);
INSERT INTO attribute_class(aid, classid) VALUES(3, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(4, 'en.wiktionary.org', 1, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(4, 1);
INSERT INTO attribute_class(aid, classid) VALUES(4, 2);
INSERT INTO attribute_class(aid, classid) VALUES(4, 3);
-- Affix flags
INSERT INTO attribute(aid, descr, type, editable) VALUES(5, '[Hunspell-A] prefix re-', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(5, 1);
INSERT INTO attribute_class(aid, classid) VALUES(5, 2);
INSERT INTO attribute_class(aid, classid) VALUES(5, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(6, '[Hunspell-I] prefix in-', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(6, 1);
INSERT INTO attribute_class(aid, classid) VALUES(6, 2);
INSERT INTO attribute_class(aid, classid) VALUES(6, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(7, '[Hunspell-U] prefix un-', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(7, 1);
INSERT INTO attribute_class(aid, classid) VALUES(7, 2);
INSERT INTO attribute_class(aid, classid) VALUES(7, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(8, '[Hunspell-C] prefix de-', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(8, 1);
INSERT INTO attribute_class(aid, classid) VALUES(8, 2);
INSERT INTO attribute_class(aid, classid) VALUES(8, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(9, '[Hunspell-E] prefix dis-', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(9, 1);
INSERT INTO attribute_class(aid, classid) VALUES(9, 2);
INSERT INTO attribute_class(aid, classid) VALUES(9, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(10, '[Hunspell-F] prefix con-', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(10, 1);
INSERT INTO attribute_class(aid, classid) VALUES(10, 2);
INSERT INTO attribute_class(aid, classid) VALUES(10, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(11, '[Hunspell-K] prefix pro-', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(11, 1);
INSERT INTO attribute_class(aid, classid) VALUES(11, 2);
INSERT INTO attribute_class(aid, classid) VALUES(11, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(12, '[Hunspell-V] adjective -ive', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(12, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(13, '[Hunspell-N] noun -ion', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(13, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(14, '[Hunspell-X] noun -ions', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(14, 1);
-- Hunspell-H seems to be mainly for numerals
INSERT INTO attribute(aid, descr, type, editable) VALUES(15, '[Hunspell-Y] adverb -ly', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(15, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(16, '[Hunspell-G] noun/adjective -ing', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(16, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(17, '[Hunspell-J] noun -ings', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(17, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(18, '[Hunspell-D] suffix -ed', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(18, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(19, '[Hunspell-T] suffix -est', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(19, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(20, '[Hunspell-R] suffix -er', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(20, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(21, '[Hunspell-Z] noun -ers', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(21, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(22, '[Hunspell-S] plural', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(22, 2);
INSERT INTO attribute(aid, descr, type, editable) VALUES(23, '[Hunspell-P] noun -ness', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(23, 3);
INSERT INTO attribute(aid, descr, type, editable) VALUES(24, '[Hunspell-M] suffix -''s', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(24, 2);
INSERT INTO attribute(aid, descr, type, editable) VALUES(25, '[Hunspell-B] adjective -able', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(25, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(26, '[Hunspell-L] noun -ment', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(26, 1);



INSERT INTO appuser(uid, uname) VALUES(1, 'autoconverter');
INSERT INTO appuser(uid, uname, firstname, lastname) VALUES(2, 'example', 'Example', 'User');

INSERT INTO task(tid, descr, sql, orderby) VALUES(1, 'Check all words starting with a',
  'SELECT taskw.wid FROM word taskw WHERE taskw.word LIKE ''a%''', 'w.word');

\c joukahainen_private
DELETE FROM appuser;
INSERT INTO appuser(uid, uname, firstname, lastname, pwhash, isadmin)
  VALUES(2, 'example', 'Example', 'User', 'password_hash_here', TRUE);
