# -*- coding: utf-8 -*-

# Application configuration file for Joukahainen

# Root directory of the application as seen from the web
WWW_ROOT_DIR = '/joukahainen'

# Path to module directory (Joukahainen)
MODULE_PATH_JOUKAHAINEN = 'hunspell-fi-svn/trunk/joukahainen/pylib'

# Path to module directory (Hunspell-fi tools)
MODULE_PATH_HFTOOLS = 'hunspell-fi-svn/trunk/tools/pylib'

# Path to Hunspell-fi data directory
HF_DATA = 'hunspell-fi-svn/trunk/data'

# Path to template directory
TEMPLATE_PATH = 'hunspell-fi-svn/trunk/joukahainen/templates'

# Global password salt
PW_SALT = u'XPmCefh'

# Session timeout in seconds
SESSION_TIMEOUT = 7200

# Database connection parameters
DBHOST = 'localhost'
DB_PORT = 5432
DB_DATABASE = 'joukahainen'
DB_USER = 'joukahainen'
DB_PASSWORD = 'write_password_here'
