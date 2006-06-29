-- This file contains commands to create the database
-- schema for the private part of Joukahainen.

-- Prepare the database
\c template1
DROP DATABASE joukahainen_private;
CREATE DATABASE joukahainen_private WITH encoding='UTF-8';
\c joukahainen_private

-- Application user. Dynamic.
CREATE TABLE appuser (
  uid integer PRIMARY KEY, -- user identifier
  uname varchar UNIQUE NOT NULL, -- username
  firstname varchar, -- first name
  lastname varchar, -- last name
  email varchar, -- email address
  pwhash char(40), -- password hash
  regtime timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, -- user registration time
  disabled boolean NOT NULL DEFAULT FALSE, -- login disabled
  session_key char(40), -- session key
  session_exp timestamp -- session expiration time
);

-- Grant privileges
GRANT SELECT, UPDATE on appuser TO joukahainen;
