-- This file contains commands to create the database
-- schema for Joukahainen

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

-- A word attribute. Static.
CREATE TABLE attribute (
  aid integer PRIMARY KEY, -- attribute identifier
  name varchar NOT NULL, -- attribute name
  type integer NOT NULL, -- attribute type (references to types in program code)
  editable boolean NOT NULL -- is this attribute editable by users?
);

-- Attribute-wordclass relation. Static.
CREATE TABLE attribute_class (
  aid integer REFERENCES attribute, -- word attribute
  classid integer references wordclass, -- word class
  PRIMARY KEY (aid, classid)
);

-- A word. Dynamic.
CREATE TABLE word (
  wid SERIAL PRIMARY KEY, -- word identifier
  word varchar NOT NULL, -- word
  class integer NOT NULL REFERENCES wordclass -- word class
);

-- Word attribute value (string). Dynamic.
CREATE TABLE string_attribute_value (
  wid integer NOT NULL REFERENCES word, -- word
  aid integer NOT NULL REFERENCES attribute, -- attribute
  value varchar, -- value
  PRIMARY KEY (wid, aid)
);


-- Grant privileges
GRANT SELECT ON language, wordclass, attribute, attribute_class TO joukahainen;
GRANT ALL ON word, string_attribute_value TO joukahainen;

