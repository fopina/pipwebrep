from flask import Flask, session, redirect, url_for, escape, request, render_template, flash
from functools import wraps
from PIPStuff import PIPStuff
import settings

import java.lang.Class
java.lang.Class.forName(settings.DRIVER)

FLASH_ERROR = 'danger'

app = Flask(__name__)

# dirty fix for app root_path because module is loaded as "__builtin__" (in Tomcat)
# as flask is in the app WEB-INF
# sys.modules['flask'].__file__
# is something like
# /usr/tomcat6/webapps/jyWebRep/WEB-INF/lib-python/flask/__init__.py
import sys,os
app.root_path = os.path.abspath(os.path.dirname(sys.modules['flask'].__file__)+'/../../../')

def requires_login():
	def wrapper(f):
		@wraps(f)
		def wrapped(*args, **kwargs):
			if 'profile' not in session:
				return redirect(url_for('login'))
			return f(*args, **kwargs)
		return wrapped
	return wrapper

@app.route('/')
@requires_login()
def index():
	return render_template('main.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		profile = PIPStuff(settings.URL, request.form['username'], request.form['password'])
		try:
			profile.connect()
			session['profile'] = profile
		except java.sql.SQLException, sqle:
			flash(sqle.message, FLASH_ERROR)
		except:
			flash('Login Failed', FLASH_ERROR)

		return redirect(url_for('index'))

	return render_template('login.html')

@app.route('/logout')
def logout():
	session.pop('profile', None)
	return redirect(url_for('index'))

@app.route('/query', methods=['GET', 'POST'])
@requires_login()
def query():
	if request.method != 'POST':
		return redirect(url_for('index'))
	if 'query' not in request.form:
		return redirect(url_for('index'))

	profile = session['profile']
	stmt = request.form['query']

	try:
		headers, results = profile.executeSQL(stmt)
		return render_template('query.html', query = stmt, headers = headers, results = results)
	except java.sql.SQLException, sqle:
		flash(sqle.message, FLASH_ERROR)
	except:
		flash('Login Failed', FLASH_ERROR)

	return redirect(url_for('query'))
	

@app.errorhandler(500)
def internal_error(error):
	return repr(error)

@app.errorhandler(404)
def not_found(error):
	return repr(error)

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?R1'


if __name__ == '__main__':
	app.run()
