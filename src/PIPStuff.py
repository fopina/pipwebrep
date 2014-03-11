from java.sql import DriverManager,Statement,ResultSet,ResultSetMetaData

# stupid bug...
# make sure any module that uses PIPStuff calls Class.forName
# import java.lang.Class
# java.lang.Class.forName(DRIVER_NAME)

class PIPUser():
	def __init__(self, dburl, dbuser, dbpass):
		self._dburl = dburl
		self.username = dbuser
		self.password = dbpass
	
	def connect(self):
		return DriverManager.getConnection(self._dburl,self.username,self.password)

	def executeQuery(self, sqlQry, maxrows = None, values = []):
		connection = self.connect()

		statement = connection.prepareStatement(sqlQry, ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY)

		self._updateStatement(statement, values)

		if maxrows:
			statement.setMaxRows(maxrows)
			statement.setFetchSize(maxrows)
		rs = statement.executeQuery()
		rsmd = rs.getMetaData()

		headers, rows = ([],[])

		for i in xrange(1, rsmd.getColumnCount()+1):
			headers.append(rsmd.getColumnLabel(i))

		while rs.next():
			cols = []
			for i in xrange(1, rsmd.getColumnCount()+1):
				cols.append(rs.getString(i))
			rows.append(cols)

		return (headers,rows)

	def executeUpdate(self, sql, values = []):
		connection = self.connect()

		statement = connection.prepareStatement(sql, ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY)

		self._updateStatement(statement, values)

		rows = statement.executeUpdate()

		return rows

	def _updateStatement(self, statement, values):
		if not values:
			return

		for i in xrange(len(values)):
			if values[i] == None:
				statement.setString(i+1, '')
			else:
				statement.setString(i+1, values[i])		