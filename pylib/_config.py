# -*- coding: utf-8 -*-

# Application configuration file for Joukahainen

# Installation directory
INSTALLATION_DIRECTORY = u'hunspell-fi-svn/trunk/joukahainen'

# Root directory of the application as seen from the web
WWW_ROOT_DIR = '/joukahainen'

# Global password salt
PW_SALT = u'XPmCefh'

# Session timeout in seconds
SESSION_TIMEOUT = 7200

# User interface language
LANG = u'fi'

# This option can be used to prevent non-admin users from logging in when
# maintenance work is being done
ONLY_ADMIN_LOGIN_ALLOWED = False

# Database connection parameters
DBHOST = 'localhost'
DB_PORT = 5432
DB_PUBLIC_DATABASE = 'joukahainen'
DB_PRIVATE_DATABASE = 'joukahainen_private'
DB_USER = 'joukahainen'
DB_PASSWORD = 'write_password_here'
