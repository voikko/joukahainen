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

-- Insert new data
INSERT INTO wordclass(classid, name) VALUES(1, 'general');
INSERT INTO attribute_type(type, descr) VALUES(1, 'string');
INSERT INTO attribute_type(type, descr) VALUES(2, 'flag');
INSERT INTO attribute(aid, descr, type, editable) VALUES(1, 'short explanation', 1, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(1, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(2, 'incorrect word', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(2, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(3, 'should be checked', 2, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(3, 1);
INSERT INTO attribute(aid, descr, type, editable) VALUES(4, 'en.wiktionary.org', 1, TRUE);
INSERT INTO attribute_class(aid, classid) VALUES(4, 1);


INSERT INTO appuser(uid, uname) VALUES(1, 'autoconverter');
INSERT INTO appuser(uid, uname, firstname, lastname) VALUES(2, 'example', 'Example', 'User');

INSERT INTO task(tid, descr, sql, orderby) VALUES(1, 'Check all words starting with a',
  'SELECT taskw.wid FROM word taskw WHERE taskw.word LIKE ''a%''', 'w.word');

\c joukahainen_private
DELETE FROM appuser;
INSERT INTO appuser(uid, uname, firstname, lastname, pwhash, isadmin)
  VALUES(2, 'example', 'Example', 'User', 'password_hash_here', TRUE);
