# -*- coding: utf-8 -*-
from java.sql import DriverManager,Statement,ResultSet,ResultSetMetaData
from datetime import date,time

# stupid bug...
# make sure any module that uses PIPStuff calls Class.forName
# import java.lang.Class
# java.lang.Class.forName(DRIVER_NAME)

TYPE_DATE = 'DATE'
TYPE_BOOL = 'BIT'
TYPE_INT = 'BIGINT'
TYPE_DECIMAL = 'DECIMAL'
TYPE_TIME = 'TIME'
TYPE_VARCHAR = 'VARCHAR2'
TYPE_DOUBLE = 'DOUBLE'
TYPE_TIME = 'TIME'

class PIPUser():
	def __init__(self, dburl, dbuser, dbpass):
		self._dburl = dburl
		self.username = dbuser
		self.password = dbpass
	
	def connect(self):
		return DriverManager.getConnection(self._dburl,self.username,self.password)

	def execute_query(self, sqlQry, maxrows = None, values = [], metadata = False):
		connection = self.connect()

		statement = connection.prepareStatement(sqlQry, ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY)

		self._update_statement(statement, values)

		if maxrows:
			statement.setMaxRows(maxrows)
			statement.setFetchSize(maxrows)
		rs = statement.executeQuery()
		rsmd = rs.getMetaData()

		headers, types, rows = ([],[], [])
	
		for i in xrange(1, rsmd.getColumnCount()+1):
			headers.append(rsmd.getColumnLabel(i))
			types.append(rsmd.getColumnTypeName(i))

		while rs.next():
			cols = []
			for i in xrange(1, rsmd.getColumnCount()+1):
				cols.append(self._proper_rs_get_column(rs, i, types[i-1]))
			rows.append(cols)

		if metadata:
			return (headers, types, rows)
		else:
			return rows

	def execute_update(self, sql, values = []):
		connection = self.connect()

		statement = connection.prepareStatement(sql, ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY)

		self._update_statement(statement, values)

		rows = statement.executeUpdate()

		return rows

	def _update_statement(self, statement, values):
		if not values:
			return

		for i in xrange(len(values)):
			if values[i] == None:
				statement.setString(i+1, '')
			else:
				statement.setString(i+1, values[i])

	def _proper_rs_get_column(self, rs, column, type):
		if type == TYPE_DATE:
			return date.fromtimestamp(rs.getDate(column).getTime()/1000)
		if type == TYPE_BOOL:
			return rs.getBoolean(column)
		if type == TYPE_INT:
			return rs.getInt(column)
		if type == TYPE_DECIMAL:
			return rs.getDouble(column)
		if type == TYPE_DOUBLE:
			return rs.getDouble(column)
		if type == TYPE_TIME:
			javatime = rs.getTime(column)
			return time(javatime.hours, javatime.minutes, javatime.seconds)

		val = rs.getString(column)

		if val == None:
			val = ''

		return val