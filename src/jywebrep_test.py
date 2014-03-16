from __future__ import with_statement
import jywebrep
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
		pass

	def login(self, username, password):
		return self.app.post('/login', data=dict(
			username=username,
			password=password
		), follow_redirects=True)

	def logout(self):
		return self.app.get('/logout', follow_redirects=True)

if __name__ == '__main__':
	unittest.main()