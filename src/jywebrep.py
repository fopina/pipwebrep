from flask import Flask, session, redirect, url_for, escape, request, render_template, flash
from functools import wraps
from PIPStuff import PIPUser
import settings

import java.lang.Class
java.lang.Class.forName(settings.DRIVER)

FLASH_ERROR = 'danger'
FLASH_SUCCESS = 'success'

app = Flask(__name__)
app.config.from_object('settings')

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


@app.route('/sqleditor', methods=['GET', 'POST'])
@requires_login()
def sqleditor():
	session['tab'] = 2
	profile = session['profile']

	if request.method == 'POST': # save query
		form = request.form

		if not form.get('id'):
			flash('Report ID is required!', FLASH_ERROR)
			return render_template('sqleditor.html', form = form)

		_, queries = profile.executeQuery(
					"SELECT QID,SCOPE,USR FROM WEBSQLQRY WHERE QID=?",
					1,
					[form['id']]
					)

		scope = settings.SCOPE_PRIVATE if form.get('scope') else settings.SCOPE_PUBLIC

		# report already exists
		if queries:
			report = queries[0]

			if form.get('confirmsave') != 'confirm':
				return render_template('sqleditor.html', form = form, confirm_required = True)

			# this should be in a PIP DQ trigger for atomicity, but...
			if (report[1] == settings.SCOPE_PRIVATE) and (report[2] != profile.username):
				flash('%s is private and not yours' % report[1], FLASH_ERROR)
				return render_template('sqleditor.html', form = form)

			try:
				profile.executeUpdate(
					'UPDATE WEBSQLQRY SET SCOPE = ?, DES = ? WHERE QID = ?',
					[ scope, form['description'], form['id'] ],
					)

				profile.executeUpdate(
					'UPDATE WEBSQLQRY SET QUERY = ? WHERE QID = ?',
					[ form['squery'], form['id'] ],
					)
			except java.sql.SQLException, sqle:
				flash(sqle.message, FLASH_ERROR)
				return render_template('sqleditor.html', form = form)

			flash('%s updated!' % form['id'], FLASH_SUCCESS)
		else:
			try:
				profile.executeUpdate(
					'INSERT INTO WEBSQLQRY (QID,SCOPE,DES) VALUES (?,?,?)',
					[ form['id'], scope, form['description'] ],
					)

				profile.executeUpdate(
					'UPDATE WEBSQLQRY SET QUERY = ? WHERE QID = ?',
					[ form['squery'], form['id'] ],
					)
			except java.sql.SQLException, sqle:
				flash(sqle.message, FLASH_ERROR)
				return render_template('sqleditor.html', form = form)

			flash('%s created!' % form['id'], FLASH_SUCCESS)
		
		return render_template('sqleditor.html', form = form)
	else:
		form = {}

		if 'edit' in request.args:
				_, queries = profile.executeQuery(
					"SELECT QID,DES,SCOPE FROM WEBSQLQRY WHERE QID=?",
					1,
					[request.args['edit']]
					)

				if not queries:
					flash('Report %s not found' % request.args['edit'], FLASH_ERROR)
					return redirect(url_for('reports'))

				report = queries[0]
				form['id'] = report[0]
				form['description'] = report[1]
				form['scope'] = True if report[2] == settings.SCOPE_PRIVATE else False

				_, queries = profile.executeQuery(
					"SELECT QUERY FROM WEBSQLQRY WHERE QID=?",
					1,
					[request.args['edit']]
					)

				if queries and queries[0][0]:
					session['query'] = queries[0][0]
				else:
					session['query'] = ''

		form['squery'] = session['query']

		return render_template('sqleditor.html', form = form)

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
