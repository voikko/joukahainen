-- This file contains commands to create the database
-- schema for the (possibly) public part of Joukahainen.

-- Prepare the database
\c template1
DROP DATABASE joukahainen;
CREATE DATABASE joukahainen WITH encoding='UTF-8';
\c joukahainen

-- A (natural) language. This table is currently not used. Static.
CREATE TABLE language (
  langid integer PRIMARY KEY, -- language identifier
  name varchar NOT NULL -- name of the language
);

-- A word class. Static.
CREATE TABLE wordclass (
  classid integer PRIMARY KEY, -- class identifier
  name varchar NOT NULL -- name of the word class
);

-- A word attribute type. Static.
CREATE TABLE attribute_type (
  type integer PRIMARY KEY, -- attribute type identifier
  descr varchar NOT NULL -- attribute type description
);

-- A word attribute. Static.
CREATE TABLE attribute (
  aid integer PRIMARY KEY, -- attribute identifier
  descr varchar NOT NULL, -- attribute description
  type integer NOT NULL REFERENCES attribute_type, -- attribute type
  editable boolean NOT NULL -- is this attribute editable by users?
);

-- Attribute-wordclass relation. Static.
CREATE TABLE attribute_class (
  aid integer REFERENCES attribute, -- word attribute
  classid integer references wordclass, -- word class
  PRIMARY KEY (aid, classid)
);

-- Application user (public parts only). Static.
CREATE TABLE appuser (
  uid integer PRIMARY KEY, -- user identifier
  uname varchar UNIQUE NOT NULL, -- username
  firstname varchar, -- first name
  lastname varchar, -- last name
  email varchar -- email address
);

-- A word. Dynamic.
CREATE TABLE word (
  wid SERIAL PRIMARY KEY, -- word identifier
  word varchar NOT NULL, -- word
  class integer NOT NULL REFERENCES wordclass, -- word class
  cuser integer REFERENCES appuser, -- user who created this word
  ctime timestamp DEFAULT CURRENT_TIMESTAMP -- creation time
);

-- Edit event. Dynamic.
CREATE TABLE event (
  eid SERIAL PRIMARY KEY, -- event identifier
  eword integer REFERENCES word, -- word related to this event
  euser integer REFERENCES appuser, -- user who initiated the event
  etime timestamp DEFAULT CURRENT_TIMESTAMP, -- time of the event
  message varchar, -- message describing the event
  comment varchar -- user comment about the event
);

-- Word attribute value (string). Dynamic.
CREATE TABLE string_attribute_value (
  wid integer NOT NULL REFERENCES word, -- word
  aid integer NOT NULL REFERENCES attribute, -- attribute
  value varchar NOT NULL, -- value
  eevent integer REFERENCES event, -- last edit event
  PRIMARY KEY (wid, aid)
);
CREATE INDEX string_attribute_value_wid_idx ON string_attribute_value(wid);

-- Word attribute value (integer). Dynamic.
CREATE TABLE int_attribute_value (
  wid integer NOT NULL REFERENCES word, -- word
  aid integer NOT NULL REFERENCES attribute, -- attribute
  value integer NOT NULL, -- value
  eevent integer REFERENCES event, -- last edit event
  PRIMARY KEY (wid, aid)
);
CREATE INDEX int_attribute_value_wid_idx ON int_attribute_value(wid);

-- Word attribute value (flag). Dynamic.
CREATE TABLE flag_attribute_value (
  wid integer NOT NULL REFERENCES word, -- word
  aid integer NOT NULL REFERENCES attribute, -- attribute
  eevent integer REFERENCES event, -- last edit event
  PRIMARY KEY (wid, aid)
);
CREATE INDEX flag_attribute_value_wid_idx ON flag_attribute_value(wid);

-- Related word form or compound word. Dynamic.
CREATE TABLE related_word (
  rwid SERIAL PRIMARY KEY, -- related word form identifier
  wid integer NOT NULL REFERENCES word, -- base word
  eevent integer REFERENCES event, -- last edit event
  related_word varchar NOT NULL -- the related word form
);
CREATE INDEX related_word_wid_idx ON related_word(wid);

-- Unclassified word. Dynamic.
CREATE TABLE raw_word (
  word varchar PRIMARY KEY NOT NULL, -- word
  info varchar, -- classification or other similar information
  notes varchar, -- notes about the word
  processed boolean NOT NULL DEFAULT FALSE -- is the word already processed
);

-- Vocabulary editing task. Static.
CREATE TABLE task (
  tid integer PRIMARY KEY, -- task identifier
  descr varchar NOT NULL, -- task description
  sql varchar NOT NULL, -- SQL query returning the list of widS that are part of this task
  orderby varchar NOT NULL -- SQL ORDER BY statement for sorting the words
);

-- Words processed in a task. Dynamic.
CREATE TABLE task_word (
  tid integer NOT NULL REFERENCES task, -- task
  wid integer NOT NULL REFERENCES word, -- word
  uid integer REFERENCES appuser, -- user who processed the word
  ctime timestamp DEFAULT CURRENT_TIMESTAMP -- record creation time
);

-- Grant privileges
GRANT SELECT ON language, wordclass, attribute, attribute_class, attribute_type TO joukahainen;
GRANT SELECT, UPDATE on word_wid_seq, related_word_rwid_seq, event_eid_seq TO joukahainen;
GRANT ALL ON word, string_attribute_value, int_attribute_value, flag_attribute_value, appuser,
  related_word, event, raw_word, task, task_word TO joukahainen;
-- If you have an automated backup system, it can back up the main database using following privileges:
-- GRANT SELECT ON language, wordclass, attribute, attribute_class, attribute_type,
--                 word_wid_seq, related_word_rwid_seq, event_eid_seq,
--                 word, string_attribute_value, int_attribute_value, flag_attribute_value, appuser,
--                 related_word, event, raw_word, task, task_word TO joukahainenbackup;
