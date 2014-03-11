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

	def executeSQL(self, sqlQry, maxrows = None):
		connection = self.connect()
		statement = connection.createStatement(ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY)
		if maxrows:
			statement.setMaxRows(maxrows)
			statement.setFetchSize(maxrows)
		rs = statement.executeQuery(sqlQry)
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