# -*- coding: utf-8 -*-

# Application configuration file for Joukahainen

# Installation directory
INSTALLATION_DIRECTORY = u'hunspell-fi-svn/trunk/joukahainen'

# Root directory of the application as seen from the web
WWW_ROOT_DIR = '/joukahainen'

# URL prefix for Wiki links
WIKI_URL = u'http://fi.wiktionary.org/wiki/'

# Global password salt
PW_SALT = u'XPmCefh'

# Session timeout in seconds
SESSION_TIMEOUT = 7200

# User interface language
LANG = u'fi'

# Database connection parameters
DBHOST = 'localhost'
DB_PORT = 5432
DB_PUBLIC_DATABASE = 'joukahainen'
DB_PRIVATE_DATABASE = 'joukahainen_private'
DB_USER = 'joukahainen'
DB_PASSWORD = 'write_password_here'
