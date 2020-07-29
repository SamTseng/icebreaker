#/usr/bin/env python
# -*- coding: utf-8 -*-
# Written by Yuen-Hsien Tseng on 2018/12/14

import sys, re
import sqlite3

class Next_Doc():
	'''
    Given a file containing multiple fields in (tab|comma)-delimited format,
    return a row each time nextdoc() is called.
	'''
	def __init__(self, InFile='jokes.txt', delimiter='\t'):
		self.fn = InFile
		self.delimiter = delimiter
		self.first_line = ''

		# try to read the first line to know the file format
		with open(InFile, encoding='UTF8') as f:
			self.first_line = f.readline()
	# The with statement automatically closes the file when the block ends.
	# see: https://stackoverflow.com/questions/1904394/read-only-the-first-line-of-a-file
		if re.match(r'^###', self.first_line): # Chen_GwoDong_joke.txt
			self.delimiter = '###\n'
			with open(InFile, encoding='UTF8') as f:
				self.lines = f.read().split(self.delimiter)
		else:
			self.fh = open(InFile, encoding='UTF8')


	def __iter__(self):
		if re.match(r'^###', self.first_line): # Chen_GwoDong_joke.txt
			for line in self.lines:
				if len(line) < 20: continue
				yield(['GwoDong', line])
		else:
			for line in self.fh.readlines():
				LI = line.split(self.delimiter) 
				LI[-1] = LI[-1].strip()
				yield(LI)
		
if __name__ == "__main__":
# After running:
#   python joke2txt.py ../jokes_3691.xlsx > jokes.txt
# Test the functionality of this module, by running:
#   python Next_Doc.py jokes.txt
# On 2019/06/02
# python Next_Doc.py /Users/sam/GoogleDrive/AnacondaProjects/FBCrawler/Chen_GwoDong_joke.txt | more

	conn = sqlite3.connect('Chat_DB.db')
	cur = conn.cursor()
	cur.execute("SELECT jokeID, txt FROM TjokeBase")

	W = cur.fetchall()

	for index in range(len(W)):
		source = W[index][0] 
		joke = W[index][1]
		print("%s: %s " % (source, joke))

	#print("%s : %s : %s" % (ID, i, joke))
	

	'''
	for i, (source, joke) in enumerate(nxtd):
		print("%s : %s : %s" % (source, i, joke))
	'''