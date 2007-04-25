-- This file contains commands to create the database
-- schema for the private part of Joukahainen.

-- Prepare the database
\c template1
DROP DATABASE joukahainen_private;
CREATE DATABASE joukahainen_private WITH encoding='UTF-8';
\c joukahainen_private

-- Application user. Dynamic.
CREATE TABLE appuser (
  uid SERIAL PRIMARY KEY, -- user identifier
  uname varchar UNIQUE NOT NULL, -- username
  firstname varchar, -- first name
  lastname varchar, -- last name
  email varchar, -- email address
  pwhash char(40), -- password hash
  regtime timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, -- user registration time
  disabled boolean NOT NULL DEFAULT FALSE, -- login disabled
  isadmin boolean NOT NULL DEFAULT FALSE, -- is an administrator
  session_key char(40), -- session key
  session_exp timestamp -- session expiration time
);

-- Guest user access control. Dynamic.
CREATE TABLE guestaccess (
  ip inet PRIMARY KEY, -- ip address of the guest system
  last_access_date date NOT NULL DEFAULT CURRENT_DATE, -- date of the last access
  access_count integer NOT NULL DEFAULT 1 -- number of times the guest has used a
                                          -- protected resource within last_access_date
);

-- Grant privileges
GRANT ALL on appuser, guestaccess TO joukahainen;
GRANT SELECT, UPDATE on appuser_uid_seq TO joukahainen;
