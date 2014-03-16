from __future__ import with_statement
import jywebrep
import flask
import unittest

TESTID = '1'
TESTPWD = 'xxx'

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
		assert 'Server Error - invalid user ID' in rv.data

	def test_login_logout(self):
		rv = self.login(TESTID, TESTPWD)
		assert '<title>Reports</title>' in rv.data
		rv = self.logout()
		assert '<form method="POST" action="login"' in rv.data

	def test_pipstuff_sql(self):
		with self.app as c:
			rv = c.post('/login', data = dict(
				username = TESTID,
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
		

	def login(self, username, password):
		return self.app.post('/login', data=dict(
			username=username,
			password=password
		), follow_redirects=True)

	def logout(self):
		return self.app.get('/logout', follow_redirects=True)

if __name__ == '__main__':
	unittest.main()