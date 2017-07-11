#!/usr/bin/python3

###### get_nodes_and_edges2.py ######

import pandas as pd
import datetime
import os

def main():
	# input and output files
	infile = 'A worked at B - 20170710-2209pm.csv'
	CCfile = 'CCIHE2015-PublicDataFile.xlsx'

	now = datetime.date.today().strftime("%Y%m%d")
	nodefile = 'placement_nodes_' + now + '.csv'
	edgefile = 'placement_edges_' + now + '.csv'

	# read in data file (export this first from google sheets)
	data = pd.read_csv(infile)	
	data = data[data['Confirmed by a second reader?'] != 'exclude']
		# and inspect to make sure you got what you wanted
	data.info()

	# get schools 
	# (I know this could be more efficient, but at least it's clear, right?)
	schoolrows = data[data['School?'] == 'y']	# yes, I'm used to R, sue me
	schools = schoolrows['Worked At'].drop_duplicates()
	schools = schools.append(data['Studied At (PhD)'].drop_duplicates())
	schools = schools.drop_duplicates().dropna()
	del schoolrows

	
	# load extra info from Carnegie Classifications
	cc_labels = pd.read_excel(CCfile, sheetname='Labels', dtype='object', index_col=[0,1])
	cc_data =  pd.read_excel(CCfile, sheetname='Data', dtype='object')

	# add columns from CC_data sheet to schools
	schools = pd.merge(schools.to_frame(name='NAME'), cc_data, how='left', on=['NAME'])
	
	# add columns from (desired) CC_labels sheet to CC_data
	desired = ['BASIC2015', 'SIZESET2015', 'IPUG2015', 'IPGRAD2015', 'ENRPROFILE2015', 'UGPROFILE', 'SECTOR', 'OBEREG', 'LOCALE']
	vars = cc_labels.Variable.dropna()
	
	# Helper function to get the label of an arbitrary variable and value
	def getlabel4value(labelsheet, var, val):
		# set the query
		q = 'Variable == "{}" & Value == {}'.format(var, val)
	
		# match the value; this returns a frame with one row and two columns,
		# the column header (label) and its value (val)
		label_frame = labelsheet.query(q)
	
		# return just the string content of the second column
		return label_frame.iloc[0][1]


	# testing
	col = 'SIZESET2015'
	newcol = col + '_VAL'	
	row = schools.iloc[0]	# first school, entire row
	getlabel4value(cc_labels, col, row[col])
	
	# implementing
		
	schools.assign(newcol = lambda x: getlabel4value(cc_labels, col, x[col])

	cc_filled = CC_labels.fillna(method='ffill')
	cc_filled[cc_filled['Variable'] == 'BASIC2015']
	cc_filled.query(Variable == 'BASIC2015')
	cc_filled.

	
	
	# now for the people
	data['Label'] = data['First Name'] + ' ' + data['Last Name']
	people = data['Label'].drop_duplicates().dropna()
	
	
	
	# and export schools and people together as nodes
	nodes = people.append(schools)
	
	
	
	
