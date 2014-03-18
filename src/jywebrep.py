# -*- coding: utf-8 -*-
from flask import Flask, session, redirect, url_for, escape, request, render_template, flash, Response
from functools import wraps
from PIPStuff import PIPUser
import settings

# XLS export
import xlwt_helper
from StringIO import StringIO

# JDBC...
import java.lang.Class
java.lang.Class.forName(settings.DRIVER)

# Flask FLASH categories
FLASH_ERROR = 'danger'
FLASH_SUCCESS = 'success'

# app initializion
app = Flask(__name__)
app.config.from_object('settings')

# app version
try:
	import gitversion
	app.config['VERSION'] = gitversion.VERSION
except:
	app.config['VERSION'] = 'DEV'


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

	confirm_required = False

	if request.args.get('del'):
		if 'confirm' not in request.args:
			confirm_required = True
		else:
			try:
				profile.execute_update(
					'DELETE FROM WEBSQLQRY WHERE QID = ?',
					[ request.args['del'] ],
					)
				flash('%s deleted!' % request.args['del'], FLASH_SUCCESS)
			except java.sql.SQLException, sqle:
				flash(sqle.message, FLASH_ERROR)

	try:
		reports = profile.execute_query(
			"SELECT QID,DES,SCOPE,USR FROM WEBSQLQRY WHERE SCOPE=? or (SCOPE=? and USR=?)",
			 100,
			 [settings.SCOPE_PUBLIC, settings.SCOPE_PRIVATE, profile.username]
			 )
	except java.sql.SQLException, sqle:
		flash(sqle.message, FLASH_ERROR)
	
	return render_template('reports.html', reports = reports, confirm_required = confirm_required)


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

		queries = profile.execute_query(
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
				profile.execute_update(
					'UPDATE WEBSQLQRY SET SCOPE = ?, DES = ? WHERE QID = ?',
					[ scope, form['description'], form['id'] ],
					)

				profile.execute_update(
					'UPDATE WEBSQLQRY SET QUERY = ? WHERE QID = ?',
					[ form['squery'], form['id'] ],
					)
			except java.sql.SQLException, sqle:
				flash(sqle.message, FLASH_ERROR)
				return render_template('sqleditor.html', form = form)

			flash('%s updated!' % form['id'], FLASH_SUCCESS)
		else:
			try:
				profile.execute_update(
					'INSERT INTO WEBSQLQRY (QID,SCOPE,DES) VALUES (?,?,?)',
					[ form['id'], scope, form['description'] ],
					)

				profile.execute_update(
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
				queries = profile.execute_query(
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

				queries = profile.execute_query(
					"SELECT QUERY FROM WEBSQLQRY WHERE QID=?",
					1,
					[request.args['edit']]
					)

				if queries and queries[0][0]:
					session['query'] = queries[0][0]
				else:
					session['query'] = ''

		form['squery'] = session.get('query','')

		return render_template('sqleditor.html', form = form)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		environ = request.form['environ'].split(':')
		host = environ[0]
		port = environ[1]
		profile = PIPUser(settings.URL % (host, port), request.form['username'], request.form['password'])
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

	excel = 'excel' in request.args

	if request.method == 'POST':
		query = request.form.get('query')
		try:
			maxrows = int(request.form['maxrows'])
		except:
			pass
	else:
		if 'run' in request.args:
			queries = profile.execute_query(
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
		headers, _, results = profile.execute_query(query, maxrows, metadata = True)
		if not excel:
			return render_template('query.html', query = query, headers = headers, results = results)
		else:
			filename = request.args.get('run','Report')
			
			res = StringIO()

			xlwt_helper.output(
				res, filename, headers, results,
				footer_text = 'jyWepRep v' + str(app.config['VERSION']),
				footer_link = 'https://github.com/fopina/pipwebrep/'
				)

			return Response(res.getvalue(), mimetype = 'application/octect-stream', headers = { 'Content-Disposition': 'attachment; filename=' + filename + '.xls' })
	except java.sql.SQLException, sqle:
		flash(sqle.message, FLASH_ERROR)
	except Exception, exp:
		print repr(exp)
		raise

	return redirect(url_for('query'))
	

@app.errorhandler(500)
def internal_error(error):
	return repr(error)

@app.errorhandler(404)
def not_found(error):
	return repr(error)

# set the secret key.  keep this really secret:
app.secret_key = settings.SECRET_KEY


if __name__ == '__main__':
	app.run()
