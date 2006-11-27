#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2006 Harri Pitkänen (hatapitk@iki.fi)
# This file is part of Joukahainen, a vocabulary management application

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

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

# ====== Settings ======

# URLs and dump directories
JOUKAHAINEN_URL = u'http://joukahainen.lokalisointi.org'
JOUKAHAINEN_VOC_URL = u'http://localhost/joukahainen/sanastot'
VOC_DUMP_DIR = u'/tmp/d/voc'
DB_DUMP_DIR = u'/tmp/d/db'
VOCABULARY_INDEX = u'/tmp/d/update-index-1'

# Commands
PGDUMP_COMMAND = u'/usr/lib/postgresql/8.1/bin/pg_dump'
WGET_COMMAND = u'wget'

# Database information
DB_NAME = u'joukahainen'
DB_PORT = u'5432'

# Special vocabularies, format (id, name, description)
SPECIAL_VOCS = [
	(15, u'atk', u'Tietotekniikan erikoissanasto'),
	(19, u'kasvatustiede', u'Kasvatustieteen erikoissanasto'),
	(33, u'laaketiede', u'Lääketieteen erikoissanasto'),
	(36, u'matluonnontiede', u'Matematiikan, fysiikan ja kemian erikoissanasto'),
	(35, u'vieraskieliset', u'Vieraskieliset sanat ja nimet')
]

# ====== Imports ======

import os
import subprocess
import datetime
import codecs

# ====== Functions ======

# Dumps the contents of the database to the given file
def dump_database(filename):
	dbfile = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0644)
	subprocess.call([PGDUMP_COMMAND, u'-F', u'c', u'-p', DB_PORT, DB_NAME], stdout=dbfile)
	os.close(dbfile)

# Dumps the contents of the default vocabulary to a file
def dump_default_vocabulary(filename):
	subprocess.call([WGET_COMMAND, u'-q', JOUKAHAINEN_URL + u'/malaga/default', u'-O', filename])

# Dumps the contents of a special vocabulary with specific id to a file
def dump_special_vocabulary(voc_id, filename):
	subprocess.call([WGET_COMMAND, u'-q', JOUKAHAINEN_URL + (u'/malaga/special?aid=%i' % voc_id),
	                 u'-O', filename])

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
	indexfile.write(u'[lex]\n')
	indexfile.write(u'%s/%s\n' % (JOUKAHAINEN_VOC_URL, filename))
	indexfile.write(u'%s\n' % localpath)
	indexfile.write(u'%s\n' % update_date)
	indexfile.write(u'%s\n\n' % description)

# Removes a file or symbolic link if it exists.
def remove(filename):
	if os.access(filename, os.F_OK):
		os.unlink(filename)


# ====== Main program ======

indexfile = codecs.open(VOCABULARY_INDEX, 'w', 'UTF-8')
cdate = current_date()

indexfile.write(u'[version]\n1\n\n')

# The default vocabulary
new_dvoc_name = VOC_DUMP_DIR + u'/' + DB_NAME + u'-' + cdate + u'.lex'
dvoc_link_name = VOC_DUMP_DIR + u'/' + DB_NAME + u'.lex'
dump_default_vocabulary(new_dvoc_name)
remove(dvoc_link_name)
os.symlink(new_dvoc_name, dvoc_link_name)
write_index_entry(indexfile, DB_NAME + u'.lex', u'sanat/' + DB_NAME + u'.lex', u'Perussanasto', cdate)

# The special vocabularies
for (voc_id, name, description) in SPECIAL_VOCS:
	new_svoc_name = VOC_DUMP_DIR + u'/' + name + u'-' + cdate + u'.lex'
	svoc_link_name = VOC_DUMP_DIR + u'/' + name + u'.lex'
	dump_special_vocabulary(voc_id, new_svoc_name)
	remove(svoc_link_name)
	os.symlink(new_svoc_name, svoc_link_name)
	write_index_entry(indexfile, name + u'.lex', u'sanat/erikoisalat/' + name + u'.lex',
	                  description, cdate)

# Database dumps
new_dbdump_name = DB_DUMP_DIR + u'/' + DB_NAME + u'-' + cdate + u'.pgdump'
dbdump_link_name = DB_DUMP_DIR + u'/' + DB_NAME + u'.pgdump'
dump_database(new_dbdump_name)
remove(dbdump_link_name)
os.symlink(new_dbdump_name, dbdump_link_name)

indexfile.close()

# Old file cleanup
for cldate in cleanup_dates():
	remove(VOC_DUMP_DIR + u'/' + DB_NAME + u'-' + cldate + u'.lex')
	for (voc_id, name, description) in SPECIAL_VOCS:
		remove(VOC_DUMP_DIR + u'/' + name + u'-' + cldate + u'.lex')
	remove(DB_DUMP_DIR + u'/' + DB_NAME + u'-' + cldate + u'.pgdump')
