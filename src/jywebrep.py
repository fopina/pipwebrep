from flask import Flask, session, redirect, url_for, escape, request, render_template, flash
from functools import wraps
from PIPStuff import PIPUser
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

@app.template_filter('pluralize')
def pluralize(number, singular = '', plural = 's'):
    if number == 1:
    	return singular
    else:
    	return plural

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
def index():
	return redirect(url_for('reports'))

@app.route('/reports')
@requires_login()
def reports():
	session['tab'] = 1
	profile = session['profile']
	reports = []

	try:
		_, reports = profile.executeQuery(
			"SELECT QID,DES,SCOPE,USR FROM WEBSQLQRY WHERE SCOPE=? or (SCOPE=? and USR=?)",
			 100,
			 [settings.SCOPE_PUBLIC, settings.SCOPE_PRIVATE, profile.username]
			 )
	except java.sql.SQLException, sqle:
		flash(sqle.message, FLASH_ERROR)
	
	return render_template('reports.html', reports = reports)


@app.route('/sqleditor')
@requires_login()
def sqleditor():
	session['tab'] = 2
	return render_template('sqleditor.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		profile = PIPUser(settings.URL, request.form['username'], request.form['password'])
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
	session.clear()
	return redirect(url_for('index'))

@app.route('/query', methods=['GET', 'POST'])
@requires_login()
def query():
	query = None
	profile = session['profile']
	maxrows = settings.DEFAULT_MAXROWS

	if request.method == 'POST':
		query = request.form.get('query')
		try:
			maxrows = int(request.form['maxrows'])
		except:
			pass
	else:
		if 'run' in request.args:
			_, queries = profile.executeQuery(
				"SELECT QUERY FROM WEBSQLQRY WHERE QID=?",
				1,
				[request.args['run']]
				)

			if not queries or not queries[0][0]:
				flash('Report %s not found' % request.args['run'], FLASH_ERROR)
				return redirect(url_for('reports'))

			query = queries[0][0]
			try:
				maxrows = int(request.args['maxrows'])
			except:
				pass

	if not query:
		return redirect(url_for('sqleditor'))

	session['query'] = query
	session['maxrows'] = maxrows

	try:
		headers, results = profile.executeQuery(query, maxrows)
		return render_template('query.html', query = query, headers = headers, results = results)
	except java.sql.SQLException, sqle:
		flash(sqle.message, FLASH_ERROR)
	except:
		flash('Query Failed', FLASH_ERROR)
		raise

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
