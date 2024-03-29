#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright 2006 - 2007 Harri Pitkänen (hatapitk@iki.fi)
# This file is part of Joukahainen, a vocabulary management application

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This script should be run daily to produce the vocabulary and database
# dumps from Joukahainen. It will also generate the update source index
# for Voikkoconfig and clean up old files to limit the server disc usage
# while still preserving enough backup files.
# Python version >= 2.4 is required.
# The script will produce no output if all operations succeed. Only error
# messages are printed. This will make it suitable for running as a daily
# cron job.
# This script should only be run in environments where untrusted users do
# not have write access to the directories containing the files to be created
# by this script. This is to avoid certain security issues that are not handled
# properly here.

# ====== Imports ======

import os
import subprocess
import datetime
import codecs
import sys
from getopt import getopt

# ====== Settings ======

optlist, args = getopt(sys.argv[1:], '', \
	['joukahainen_url=', 'dump_dir=', 'pgdump_command=', 'db_name=', 'db_port='])

for opt, val in optlist:
	if opt == '--joukahainen_url':
		JOUKAHAINEN_URL = val
	elif opt == '--dump_dir':
		DUMP_DIR = val
	elif opt == '--pgdump_command':
		PGDUMP_COMMAND = val
	elif opt == '--db_name':
		DB_NAME = val
	elif opt == '--db_port':
		DB_PORT = val

# Derived/unchanging configuration
JOUKAHAINEN_VOC_URL = JOUKAHAINEN_URL + '/sanastot'
VOC_DUMP_DIR = DUMP_DIR + '/sanastot'
DB_DUMP_DIR = DUMP_DIR + '/pgdumps'
WGET_COMMAND = 'wget'

# Special vocabularies, format (id, name, description)
SPECIAL_VOCS = [
	(15, 'atk', 'Tietotekniikan erikoissanasto'),
	(19, 'kasvatustiede', 'Kasvatustieteen erikoissanasto'),
	(33, 'laaketiede', 'Lääketieteen erikoissanasto'),
	(36, 'matluonnontiede', 'Matematiikan, fysiikan ja kemian erikoissanasto'),
	(35, 'vieraskieliset', 'Vieraskieliset sanat ja nimet')
]

# ====== Functions ======

# Dumps the contents of the database to the given file
def dump_database(filename):
	dbfile = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
	subprocess.call([PGDUMP_COMMAND, '-F', 'c', '-p', DB_PORT, DB_NAME], stdout=dbfile)
	os.close(dbfile)

# Dumps the contents of the default vocabulary to a file
def dump_default_vocabulary(filename):
	subprocess.call('"%s" -q "%s/query/wlist?listtype=xml" -O - | gzip > "%s"' % \
	                (WGET_COMMAND, JOUKAHAINEN_URL, filename), shell=True)

# The date for new files
def current_date():
	return datetime.date.today().isoformat()

# List of dates for which the saved files should be deleted. This list is somewhat random looking
# to make sure that if different cleanup algorithms are later used, they would have lower probability
# of interfering with each other by deleting all the files this one had saved.
def cleanup_dates():
	# Date from previous month (or the month before)
	d = datetime.date.today() - datetime.timedelta(days=40)
	datelist = []
	for delday in [2,3,4,5,7,8,10,11,12,13,15,16,18,19,20,22,23,24,25,27,28]:
		f = d.replace(day=delday)
		datelist.append(f.isoformat())
	return datelist

# Writes an entry to the vocabulary update index file
def write_index_entry(indexfile, filename, localpath, description, update_date):
	indexfile.write('[lex]\n')
	indexfile.write('%s/%s\n' % (JOUKAHAINEN_VOC_URL, filename))
	indexfile.write('%s\n' % localpath)
	indexfile.write('%s\n' % update_date)
	indexfile.write('%s\n\n' % description)

# Removes a file or symbolic link if it exists.
def remove(filename):
	if os.access(filename, os.F_OK):
		os.unlink(filename)


# ====== Main program ======

cdate = current_date()

# The default vocabulary
new_dvoc_name = VOC_DUMP_DIR + '/' + DB_NAME + '-' + cdate + '.xml.gz'
dvoc_link_name = VOC_DUMP_DIR + '/' + DB_NAME + '.xml.gz'
dump_default_vocabulary(new_dvoc_name)
remove(dvoc_link_name)
os.symlink(new_dvoc_name, dvoc_link_name)

# Database dumps
new_dbdump_name = DB_DUMP_DIR + '/' + DB_NAME + '-' + cdate + '.pgdump'
dbdump_link_name = DB_DUMP_DIR + '/' + DB_NAME + '.pgdump'
dump_database(new_dbdump_name)
remove(dbdump_link_name)
os.symlink(new_dbdump_name, dbdump_link_name)

# Old file cleanup
for cldate in cleanup_dates():
	remove(VOC_DUMP_DIR + '/' + DB_NAME + '-' + cldate + '.xml.gz')
	remove(DB_DUMP_DIR + '/' + DB_NAME + '-' + cldate + '.pgdump')
