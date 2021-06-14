# -*- coding: utf-8 -*-
#!/usr/bin/python3

import mysql.connector as database
import importlib.machinery
loginCredentials = importlib.machinery.SourceFileLoader('login_credentials','conf/login_credentials.py').load_module()	# load sql login credentials from an external file

class sqlhandler:
	def __init__(self):
		print ('creating sqlhandler class object (init)\n')

		# set the login credentials
		self.sqlLoginUser = loginCredentials.loginData["user"]
		self.sqlLoginPassword = loginCredentials.loginData["password"]
		self.sqlLoginHost = loginCredentials.loginData["host"]

	# retrieve / list all existing databases
	def fetchAllDB(self, verbose):
		connection = database.connect(user = self.sqlLoginUser, password = self.sqlLoginPassword, host = self.sqlLoginHost)
		cursor = connection.cursor(dictionary = True)

		cursor.execute("SHOW DATABASES")
		queryAllDB = cursor.fetchall()

		connection.close()

		# cout all found databases
		if verbose == 1:
			for row in queryAllDB:
				print (row['Database'])

		return queryAllDB

	# retrieve the tables from a DB
	def fetchAllTablesfromDB(self, sqlSelectDatabase, verbose):
		connection = database.connect(user = self.sqlLoginUser, password = self.sqlLoginPassword, host = self.sqlLoginHost, database = sqlSelectDatabase)
		cursor = connection.cursor(dictionary = True)

		cursor.execute("SHOW TABLES")
		queryAllTables = cursor.fetchall()

		connection.close()

		# cout the information
		if verbose == 1:
			for row in queryAllTables:
				print (row['Tables_in_' + sqlSelectDatabase])

		return queryAllTables

	# TODO: change this function so it can only fetch a certain amount of data as well as
	#		only retrieve the column types ("SHOW COLUMNS ...")
	# fetch data from a given table
	def fetchTableContent(self, sqlSelectDatabase, sqlSelectTable, verbose):
		connection = database.connect(user = self.sqlLoginUser, password = self.sqlLoginPassword, host = self.sqlLoginHost, database = sqlSelectDatabase)
		cursor = connection.cursor()

		# fetch/print the header (table column names)
		cursor.execute("SHOW COLUMNS FROM " + sqlSelectTable)
		fetchTableHeader = cursor.fetchall()

		if verbose == 1:
			for row in fetchTableHeader:
				print(f"{row[0]:>20} ", end = '')
			print('\n-----------------------------------------------------------------------------------')

		# fetch/print the table column data
		cursor.execute("SELECT * FROM " + sqlSelectTable)
		fetchTableContentData = cursor.fetchall()

		connection.close()

		# cout the table information
		if verbose == 1:
			for i in range(len(fetchTableContentData)):
				print(fetchTableContentData[i])
				#print(f"{str(fetchTableContentData[0][i]):>20} ", end = '')

		return fetchTableContentData, fetchTableHeader

	# insert data into a Table
	def insertIntoTable(self, sqlSelectDatabase, insertStatement, insertData):
		connection = database.connect(user = self.sqlLoginUser, password = self.sqlLoginPassword, host = self.sqlLoginHost, database = sqlSelectDatabase)
		cursor = connection.cursor()
		cursor.execute(insertStatement, insertData)
		connection.commit()
		connection.close()

	# create a new table
	def createTable(self, sqlSelectDatabase, tableName, columnInfo):
		connection = database.connect(user = self.sqlLoginUser, password = self.sqlLoginPassword, host = self.sqlLoginHost, database = sqlSelectDatabase)
		cursor = connection.cursor()

		# check, whether the table already exists
		getAllTables = self.fetchAllTablesfromDB(sqlSelectDatabase, 0)
		tableFound = False

		for i in getAllTables:
			if i['Tables_in_'+sqlSelectDatabase] == tableName:
				print('table', tableName, "already exists in the DB")
				tableFound = True
				break

		if tableFound == False:
			cursor.execute("CREATE TABLE " + tableName + " (" + columnInfo + ")")

		connection.close()

	# delete a table
	def dropTable(self, sqlSelectDatabase, deleteTableName):
		connection = database.connect(user = self.sqlLoginUser, password = self.sqlLoginPassword, host = self.sqlLoginHost, database = sqlSelectDatabase)
		cursor = connection.cursor()
		sql = "DROP TABLE " + deleteTableName
		cursor.execute(sql) 
		connection.close()

	# clear(truncate) a table
	def truncateTable(self, sqlSelectDatabase, deleteTableName):
		connection = database.connect(user = self.sqlLoginUser, password = self.sqlLoginPassword, host = self.sqlLoginHost, database = sqlSelectDatabase)
		cursor = connection.cursor()
		sql = "TRUNCATE TABLE " + deleteTableName
		cursor.execute(sql) 
		connection.close()

	# export a table (into a file on the disk). This file can for example be used in phpMyadmin to import the table
	# appendOnly == 1 ... don't write 'CREATE TABLE ...' into the file (only add data to an _existing_ table in the DB)
	def exportTable(self, path, appendOnly, exportDB, exportTable):
		# write the header to the file
		f = open(path, "w")
		f.write('SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";\n')
		f.write('START TRANSACTION;\n')
		f.write('SET time_zone = "+00:00";\n\n')

		# fetch the data
		tableData, tableHeaderData = self.fetchTableContent(exportDB, exportTable, 0)

		if appendOnly == 0:
			f.write('CREATE TABLE `' + exportTable + '` (\n')

			# create a list to be able to change the entries
			tableHeaderDataList = list(tableHeaderData)

			# replacements to make it compatible using, e.g., phpMyadmin
			replacements = {
				'PRI': 'PRIMARY KEY',
				'YES': '',
				#'None': '',
				'NO': 'NOT NULL'
			}

			# iterate over the list (create and write the data to the file)
			for i in tableHeaderDataList:
				# don't end the last line with a comma
				if i != tableHeaderDataList[-1]:
					endStr = ','
				else:
					endStr = ''

				# replace certain elements in the list
				i = [replacements.get(x, x) for x in i]

				# remove all elements containing 'None' (in the table header)
				res = [j for j in i if j]

				# create the string
				full_str = ' '.join([str(elem) for elem in res])
				f.write(full_str + endStr + "\n")

			f.write(") ENGINE=InnoDB DEFAULT CHARSET=latin1;\n\n")

		# create/write the data
		#
		# header:
		f.write('INSERT INTO `' + exportTable + '` ')

		tmpStr1 = "("

		for j in tableHeaderData:
			tmpStr1 += '`' + j[0] + '`, '

		# change the ending of the string
		tmpStr1 = tmpStr1[:-2] + ")"
		f.write(tmpStr1 + " VALUES \n")

		# data:
		for count, i in enumerate(tableData):
			tmpStr2 = "("

			for k in i:
				if type(k) == int:
					tmpStr2 += "" + str(k) + ", "
				else:
					tmpStr2 += "'" + str(k) + "', "

			# change the ending of the string
			tmpStr2 = tmpStr2[:-2] + ")"

			if count == len(tableData)-1:
				f.write(tmpStr2 + ";\n")
			else:
				f.write(tmpStr2 + ",\n")

		f.write("\nCOMMIT;")

		f.close()

	# import a table from an external file on the disk into the sql DB system
	def importTable(self, path, importDB):
		# open the file; parse it line, by line
		with open(path, encoding='utf-8') as fp:
			line = fp.readline()

			while line:
				#print("{}".format(line.strip()))
				line = fp.readline()
				# TODO: IGNORE COMMENTS (lines starting with "/*" or "---"

				# 'CREATE TABLE' block
				if line.find('CREATE TABLE') != -1:
					createTableName = line.split()[2].replace('`', '')
					#print("{}".format(line.strip()))
					line = fp.readline()

					# extract column information for the creation of the table
					tableArgs = []

					while line.find(';') == -1:
						#print("> {}".format(line.strip()))
						tableArgs.append(line.strip())
						line = fp.readline()

					createArgs = ''.join(tableArgs)
					
					# create the table
					self.createTable(importDB, createTableName, createArgs)

				# 'INSERT INTO' block
				if line.find('INSERT INTO') != -1:
					tableName, returnColumns = self.extractTableHeaders(line)
					#print("return table name: ", tableName, "  |  ", returnColumns)

					# extract column information for the creation of the table
					tableArgs = []

					# create the insert data
					insertColsJoined = ", ".join(returnColumns)

					# create the correct (amount of) placeholders(%s)
					placeholder = "%s"
					placeholder = [placeholder]*len(returnColumns)
					placeholder = ", ".join(placeholder)

					insertStatement = (
						"INSERT INTO " + tableName +" (" + insertColsJoined + ") "
						"VALUES (" + placeholder + ")"
					)

					# go through each insert line of the read file
					#print("   ||>   LINE: ", line)

					# continue until the last line is reached (marked by the trailing semicolon)
					while line.strip()[-1] != ";":

						line = fp.readline()	# read the next line

						#print(line.strip()[-1], "<<<<<<<<<<")
						#print("     >> {}".format(line.strip()))
						tableArgs.append(line.strip())
						#insertData = ", ".join(self.extractInsertInformation(line))

						# extract column types (if int -> conversion in the extracted data must be performed
						# to ensure a string is in the tuple which is bein inserted into the db (stored in insertData
						dummyVar, colTypesReturn = self.fetchTableContent(importDB, tableName, 0)
						colType = []
						for var in colTypesReturn:
							colType.append(var[1])
						print("COLS: ", colType)

						insertData = self.extractInsertInformation(line, colType)
						#print(" extracted insertdata: ", insertData, "\n\n")

						#print("II: ", importDB, ", ", insertStatement, ", ", insertData)
						#print(insertData, type(insertData))

						#INSERT INTO books (isbn, title, author_id, publisher_id, year_pub, description) VALUES (%s, %s, %s, %s, %s, %s) ,  ('0553213695', 'The Metamorphosis', '1', 'None', '1991', 'None')


						#if line.find('COMMIT;') != 0:
							#print("II: ", importDB, ", ", insertStatement, ", ", insertData)
							#print(line[:-2])
							#pass
						self.insertIntoTable(importDB, insertStatement, insertData)
						#else:
							#break


	def determineEndpoint(self, processStr):
		#print("> processStr ->", processStr, "<-", sep = "")
		# first element is a number 	->	(805210407, 'The Trial', 1, 0, '1995', 'None'),
		if processStr == "'":
			searchType = "string"
			endString = "'"
		# first element is a string 	->	('0553213695', 'aa\'`\'\"aa', 1, 0, '1995', 'None'),
		else:
			searchType = "number"
			endString = ','

		return searchType, endString

	# used by 'importTable': to extract the insert statements:
	#########################################################################
	# TODO: o) fix/check escaped characters, e.g.: aa\",\'`\'\",  \'  ,aa   #
	#		o) consider all edge cases, e.g.: "(1, 2, 3, 4, 5, 6),"			#
	#		o) SQL-terminal dump: "mysqldump -u root -p bookstore > dump.sql"
	#########################################################################
	def extractInsertInformation(self, insertLine, colTypes):
		#insertLine = insertLine.replace(", '", "")
		#insertLine = insertLine.replace(" ", "").replace(",'", "")

		# cut the string between the round brackets
		#strCutStart = insertLine.find("(")
		#strCutEnd = insertLine.find(")")

		#returnString = insertLine.strip()

		#print(returnString[1:-2])

		returnString = []

		processStr = insertLine[1:-3]

		#print("\n\n\n PROCESS STR: >>", processStr, "<<", sep = "")

		searchType, endString = self.determineEndpoint(processStr[0])

		if processStr[0] == "'":
			tempStr = ""
		else:
			tempStr = processStr[0]

		i = 0
		insertPosition = 0

		while i < len(processStr):
			i += 1

			#print(" check[", i, "] >" , processStr[i], "<>", endString, "< ", sep = "")
			#print(i, sep = "")
			if processStr[i] != endString:
				tempStr += processStr[i]
			else:
				if (endString == "'" and processStr[i-1] != "\\") or endString == ',':
					#print("  >end found: ", i)
					#print("  append1||", tempStr, "||", sep = "")

					# if the read string is 'none' it must be converted to an int in case of the table
					# expecting and int as datatype in the DB (else an error is thrown)
					if colTypes[insertPosition].find("int") == 0:
						if tempStr == 'None':
							tempStr = None
						else:
							tempStr = int(tempStr)

					returnString.append(tempStr)
					tempStr = ""
					insertPosition += 1

					#print ("IIII: ", i, " LEN: ", len(processStr))
					if i+1 >= len(processStr):
						break

					if endString == ",":
						i += 1	# set position to the next element
					if endString == "'":
						i += 2	# set position to the next element

					# search the next entry level point
					while processStr[i] == " ":
						#print("skip: ", i)
						i += 1

					# determine next type (endpoints)
					searchType, endString = self.determineEndpoint(processStr[i])
					#print(" NEW ENDSTRING |", endString, "|", i, "|", processStr[i], sep = "")

					if endString == ",":
						tempStr += processStr[i]

		#print()
		#print(" >>", returnString, "<< ", len(returnString))

		return tuple(returnString)

	# used by 'importTable': extract table name and table columns from the insert string, e.g., given by
	# 'INSERT INTO `2013__2013_02_28_23_55_21` (`IP`, `Date`) VALUES'. This function would retrieve
	# '2013__2013_02_28_23_55_21' and  ['IP', 'Date'] in this case.
	def extractTableHeaders(self, insertLine):
		splitString = insertLine.split('`')
		returnTableName = splitString[1]

		# cut the string between the round brackets
		strCutStart = insertLine.find("(")
		strCutEnd = insertLine.find(")")

		# extract the column names
		returnColumns = insertLine[strCutStart+2:strCutEnd-1].replace(", `", "").split('`')

		return returnTableName, returnColumns

