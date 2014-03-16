# -*- coding: utf-8 -*-
from __future__ import with_statement
import jywebrep
import flask
import unittest

from settings import TESTUID, TESTPWD

class jyWebRepTestCase(unittest.TestCase):

	def setUp(self):
		jywebrep.app.config['TESTING'] = True
		self.app = jywebrep.app.test_client()

	def tearDown(self):
		pass

	def test_empty_session(self):
		rv = self.app.get('/', follow_redirects = True)
		assert '<form method="POST" action="login"' in rv.data

	def test_login_failed(self):
		rv = self.login('script', 'kiddie')
		assert 'ER_SV_INVLDUID' in rv.data

	def test_login_logout(self):
		rv = self.login(TESTUID, TESTPWD)
		assert '<title>Reports</title>' in rv.data
		rv = self.logout()
		assert '<form method="POST" action="login"' in rv.data

	def test_pipstuff_sql(self):
		with self.app as c:
			rv = c.post('/login', data = dict(
				username = TESTUID,
				password = TESTPWD
			), follow_redirects=True)
			profile = flask.session.get('profile')
			assert profile
			rows = profile.execute_query('SELECT CONAM from CUVAR')
			oldv = rows[0][0]
			newv = '123'
			profile.execute_update("UPDATE CUVAR SET CONAM=?", [ newv ])
			assert profile.execute_query('SELECT CONAM from CUVAR')[0][0] == newv
			profile.execute_update("UPDATE CUVAR SET CONAM=?", [ oldv ])
			assert profile.execute_query('SELECT CONAM from CUVAR')[0][0] == oldv

	def test_xls_export(self):
		# random selection of PIP fields based on types
		#               D,  T,    N     ,$  ,L    ,N.5N
		query = 'select TJD,CONAM,CORPID,%CC,CCMOD,%BWPCT from CUVAR'
		rv = self.login(TESTUID, TESTPWD)
		rv = self.app.post('/query?excel', data=dict(
			query=query,
		), follow_redirects=True)
		# XLS header
		assert rv.data[:8] == '\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
		f = open('../dist/test_export.xls','w')
		f.write(rv.data)
		f.close()

	def login(self, username, password):
		return self.app.post('/login', data=dict(
			username=username,
			password=password
		), follow_redirects=True)

	def logout(self):
		return self.app.get('/logout', follow_redirects=True)

if __name__ == '__main__':
	unittest.main()