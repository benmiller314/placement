#!/usr/bin/python3

###### get_nodes_and_edges2.py ######

import pandas as pd
import datetime
import os
import numpy as np

def main():
	# input and output files
	infile = 'Worked_At_20170711-2.csv'
	CCfile = 'CCIHE2015-PublicDataFile.xlsx'
	
	now = datetime.date.today().strftime("%Y%m%d")
	nodefile = 'placement_nodes_' + now + '.csv'
	edgefile = 'placement_edges_' + now + '.csv'
	
	# read in data file (export this first from google sheets)
	data = pd.read_csv(infile)	
	data = data[data['Confirmed by a second reader?'] != 'exclude']
	
	# clean some strings
	stringcols = data.select_dtypes(['object'])
	data[stringcols.columns] = stringcols.apply(lambda x: x.str.strip())
		# and inspect to make sure you got what you wanted)
	data.info()
	
	
	# get schools 
	# (I know this could be more efficient, but at least it's clear, right?)
	schoolrows = data[data['School?'] == 'y']	# yes, I'm used to R, sue me
	schools = schoolrows['Worked At'].drop_duplicates()
	schools = schools.append(data['Studied At (PhD)'].drop_duplicates())
	schools = schools.drop_duplicates().dropna()
	# convert to dataframe
	schools = schools.to_frame(name='NAME')
	# add a column that's all "school"
	schools['Type'] = 'school'
	del schoolrows
	
	# get non-schools
	nonschoolrows = data[data['School?'] == 'n']
	nonschools = nonschoolrows['Worked At'].drop_duplicates().dropna()
	nonschools = nonschools.to_frame(name='Worked At')
	nonschools['Type'] = 'nonschool'
	
	# get city/state for non-schools; for schools we'll do this later from CC
	mylist = ['Worked At', 'City', 'State', 'Country']
	nonschools = pd.merge(nonschools, data[mylist], how='left', on=['Worked At'])
	del nonschoolrows
	
	
	# load extra info from Carnegie Classifications
	cc_labels = pd.read_excel(CCfile, sheetname='Labels', dtype='object', index_col=[0,1])
	cc_data =  pd.read_excel(CCfile, sheetname='Data', dtype='object')
	
	# add desired columns from CC_data sheet to schools
	idcols = ['NAME', 'CITY', 'STABBR']
	desired = ['CC2000', 'BASIC2005', 'BASIC2010', 'BASIC2015', 'SIZESET2015', 'IPUG2015', 'IPGRAD2015', 'ENRPROFILE2015', 'UGPROFILE2015', 'SECTOR', 'OBEREG', 'LOCALE']
	schools = pd.merge(schools, cc_data[idcols + desired], how='left', on=['NAME'])
	schools['COUNTRY'] = np.where(schools['CITY'].notnull(), 'USA', None)
	neworder = ['NAME', 'Type', 'CITY', 'STABBR', 'COUNTRY'] + desired
	schools = schools[neworder]
	del(neworder)
	
	## add columns from (desired) CC_labels sheet to CC_data
	
		# Helper function to get the label of an arbitrary variable and value
	def getlabel4value(labelsheet, var, val):
		# set the query
		if np.isnan(val):
			return None
		else:
			q = 'Variable == "{}" & Value == {}'.format(var, val)
	
		# match the value; this returns a frame with one row and two columns,
		# the column header (label) and its value (val)
		label_frame = labelsheet.query(q)
	
		# return just the string content of the second column
		# unless it's an error
		if(label_frame.empty):
			return None
		else:
			return label_frame.iloc[0][1]
	
	
	## testing
# 	col = 'SIZESET2015'
# 	newcol = col + '_VAL'	
# 	row = schools.iloc[7]
# 	getlabel4value(cc_labels, col, row[col])
# 	
# 	## debugging
# 	q = 'Variable == "{}" & Value == {}'.format(col, row[col])
# 	label_frame = cc_labels.query(q)
# 	
	# okay, let's do this thing	
	for col in desired:
		newcol = col + '_VAL'
		kwargs = {newcol : schools.apply(lambda x: getlabel4value(cc_labels, col, x[col]), axis=1)}
		schools = schools.assign(**kwargs) 
	
	# save those new columns for ease of reference
	myvals = [x for x in list(schools) if x.endswith('_VAL')]
	
	# Get column name ready for kumu
	schools = schools.rename(columns={'NAME':'Label'})
	nonschools = nonschools.rename(columns={'Worked At':'Label',
											'City':'CITY',
											'State':'STABBR',
											'Country':'COUNTRY'})
	
	# now for the people
	data['Label'] = data['First Name'] + ' ' + data['Last Name']
	people = data['Label'].drop_duplicates().dropna()
	people = people.to_frame(name='Label')
	people['Type'] = 'person'
	
	
	# finally, export places and people together as nodes
	schools.to_csv(nodefile, index=False)
	with open(nodefile, mode='a') as f:
		nonschools.to_csv(f, index=False, header=False)
	with open(nodefile, mode='a') as f:
		people.to_csv(f, index=False, header=False)
	
	
	### And now, edges
	# studied at
	mycols = ['Label', 'Studied At (PhD)', 'Degree earned', 'Degree earned in year', 'Department', 'Name found via']
	stud_rows = data[mycols]
	stud_rows.columns=['From', 'To', 'Type', 'Degree_year', 'Department', 'Data_source']
	stud_rows = stud_rows.drop_duplicates().dropna()
	stud_rows['Data_source'] = stud_rows['Data_source'].apply(lambda x: '|'.join(x.split(", ")))
	stud_rows.insert(2, 'Label', 'studied at')
	
	# worked at
	mycols = ['Label', 'Worked At', 'Role', 'Official Title', 'Start Date', 'End Date (write "present" for ongoing)', 'Source of Information (provide URL if available)']
	work_rows = data[mycols]
	work_rows.columns=['From', 'To', 'Type', 'Title', 'Start', 'End', 'Data_source']
	work_rows = work_rows.drop_duplicates().dropna()
	work_rows['Data_source'] = work_rows['Data_source'].apply(lambda x: '|'.join(x.split(", ")))
	work_rows.insert(2, 'Label', 'worked at')
	
	# merge edges for export
	edges = pd.concat([stud_rows, work_rows], axis=0, ignore_index=True) 
	col_order = ['From', 'To', 'Label', 'Type', 'Start', 'End', 'Degree_year', 'Department', 'Data_source']
	edges = edges[col_order]
	
	# finally, export edges
	edges.to_csv(edgefile, index=False, mode='w')

# call main function
if __name__=='__main__': 
	main()


