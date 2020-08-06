import json
import mysql.connector
from mysql.connector.errors import IntegrityError
from flask import Flask, request, session, redirect

# credentials files (please don't push to github)
import credentials

# initialize flask app
app = Flask("wordhoard")


app.secret_key=credentials.SECRET_KEY

# configure msql
def get_db_conn():
	conn = mysql.connector.connect(user=credentials.DATABASE_USER,password=credentials.DATABASE_PASSWORD,host=credentials.DATABASE_HOST)
	conn.cursor().execute("USE wordhoard") # convenience
	return conn

# import my utility that loads static files and load 'em
from utils.staticserver import load_all
content = load_all("/home/ubuntu/project/static")



@app.route("/static/<file>")
def static_fetch(file):
	""" serves all the files out of the static directory at /static/ """
	if (file in content.keys() and type(content[file])==str):
		return content[file]
	else:
		return "path not found :(",404

def uses_sql(func):
	""" a helpful decorator to pass in a connection and a cursor"""
	def inner():
		conn = get_db_conn()
		curs = conn.cursor(buffered=True)
		out = func(conn,curs)
		curs.close()
		conn.close()
		return out
	inner.__name__=func.__name__
	return inner

def admin_only(func):
	""" a helpful decorator to prohibit non-admin users """
	@uses_sql
	def check_admin(conn,curs):
		if (not ("username" in session)):
			return False
		curs.execute("SELECT is_administrator FROM Users WHERE username=%s",(session["username"],))
		return curs.fetchone()[0]==1
	def inner(*args,**kwargs):
		#pylint: disable=no-value-for-parameter
		if (check_admin()): # pylint says this is wrong, but it doesn't understand how decorators work...
			return func(*args,**kwargs)
		else:
			return "you must be an administrator to access this page",403
	inner.__name__=func.__name__
	return inner

def form_has(*contents):
	""" a helpful decorator to require that a form is submitted correctly """
	def decorator(func):
		def inner(*args, **kwargs):
			if (not all(x in request.form for x in contents)):
				return "did not fully fill out form :(",400
			else:
				return func(*args,**kwargs)
		inner.__name__=func.__name__
		return inner
	return decorator

@app.route("/api/createuser",methods=["GET","POST"])
@uses_sql
@form_has("username","password")
def make_user(conn,curs):
	# make a cursor
	try:
		curs.execute("INSERT INTO Users(username,password,is_administrator) VALUES (%s,%s,0)",
			(request.form["username"], request.form["password"]))
	except IntegrityError:
		return "that user already exists!",400
	# commit changes
	conn.commit()
	# return a happy message
	return "user created"

@app.route("/api/login",methods=["GET","POST"])
@uses_sql
@form_has("username","password")
def login(conn,curs):
	""" logs in a user """
	curs.execute("SELECT COUNT(*) AS Login FROM Users WHERE username=%s AND password=%s",
		(request.form["username"],request.form["password"]))
	if(curs.fetchone()[0]):
		# log em in, they got it right
		session["username"]=request.form["username"]
		return "logged in"
	else:
		return "incorrect password!",400


@app.route("/api/whoami", methods=["GET"])
def test_login():
	if ("username" in session):
		return session["username"]
	else:
		return "i don't know who you are",400

@app.route("/api/amiadmin",methods=["GET"])
@admin_only
def test_admin():
	return "you must be admin!"

@app.route("/api/addword",methods=["GET","POST"]) # this function will run when the user requests this page
@admin_only # this function can only be run by a logged in admin
@form_has("word", "pronunciation") # this function only runs if a word is provided
@uses_sql # this function needs a database connection
def addword(conn,cursor):
	try:
		cursor.execute("INSERT INTO Words(word, pronunciation) VALUES (%s, %s)",(request.form["word"],request.form["pronunciation"]))
		conn.commit()
		return "word added",200
	except IntegrityError: # if we try to insert a word that already exists...
		return "that word is already in the database",400

@app.route("/api/updateword",methods=["GET","POST"]) # this function will run when the user requests this page
@admin_only # this function can only be run by a logged in admin
@form_has("word", "pronunciation") # this function only runs if a word is provided
@uses_sql # this function needs a database connection
def updateword(conn,cursor):
	cursor.execute("UPDATE Words SET pronunciation = %s WHERE word = %s",(request.form["pronunciation"],request.form["word"]))
	conn.commit()
	return "word updated",200

@app.route("/api/delword",methods=["GET","POST"]) # this function will run when the user requests this page
@admin_only # this function can only be run by a logged in admin
@form_has("word") # this function only runs if a word is provided
@uses_sql # this function needs a database connection
def delword(conn, cursor):
	cursor.execute("DELETE FROM Words WHERE word = %s",(request.form["word"],))
	conn.commit()
	return "word deleted",200

@app.route("/api/getsynset",methods=["GET","POST"]) # this function will run when the user requests this page
@admin_only # this function can only be run by a logged in admin
@form_has("word") # this function only runs if a word is provided
@uses_sql # this function needs a database connection
def getsynset(conn,cursor):
	try:
		cursor.execute("SELECT synset FROM Synonyms WHERE word=%s",(request.form["word"],))
		conn.commit()
		return "synsets:"+" ".join([str(x[0]) for x in cursor]),200
	except IntegrityError: # if we try to insert a word that already exists...
		return "not a member of any synsets",400

@app.route("/api/addsynset",methods=["GET","POST"]) # this function will run when the user requests this page
@admin_only # this function can only be run by a logged in admin
@form_has("synset") # this function only runs if a word is provided
@uses_sql # this function needs a database connection
def addsynset(conn,cursor):
	try:
		cursor.execute("INSERT INTO Synsets(synset) VALUES (%s)",(request.form["synset"],))
		conn.commit()
		return "synset added",200
	except IntegrityError: # if we try to insert a word that already exists...
		return "that synset is already in the database",400

@app.route("/api/delsynset",methods=["GET","POST"]) # this function will run when the user requests this page
@admin_only # this function can only be run by a logged in admin
@form_has("synset") # this function only runs if a word is provided
@uses_sql # this function needs a database connection
def delsynset(conn, cursor):
	cursor.execute("DELETE FROM Synsets WHERE synset = %s",(request.form["synset"],))
	conn.commit()
	return "word deleted",200

@app.route("/api/assocword",methods=["GET","POST"]) # this function will run when the user requests this page
@admin_only # this function can only be run by a logged in admin
@form_has("synset","word") # this function only runs if a word is provided
@uses_sql # this function needs a database connection
def assocword(conn, cursor):
	try:
		cursor.execute("INSERT INTO Synonyms(word,synset) VALUES (%s, %s)",(request.form["word"],request.form["synset"]))
		conn.commit()
		return "Synonyms set",200
	except ValueError:
		return "Synonyms set is not valid",400

@app.route("/api/disassocword",methods=["GET","POST"]) # this function will run when the user requests this page
@admin_only # this function can only be run by a logged in admin
@form_has("synset","word") # this function only runs if a word is provided
@uses_sql # this function needs a database connection
def disassocword(conn, cursor):
	cursor.execute("DELETE FROM Synonyms WHERE word = %s AND synset = %s",((request.form["word"]),request.form["synset"]))
	conn.commit()
	return "Synonyms Removed",200

def sanitize(string):
	for c in string:
		o = ord(c)
		if ((o<ord('a') or o>ord('z')) and not o in "-,'"):
			raise ValueError("strings should only contain lowercase letters.")

class FeatureSet(set):
	""" set plus utility functions """
	def newName(self):
		# time to pick a new feature name
		if (len(self)==0):
			self.add("rA")
			return "rA"
		old = max(self)
		new = old[:-1]+chr(ord(old[-1])+1)
		if (new.isalpha()):
			self.add(new)
			return new
		else:
			raise ValueError("Out of feature names! Why are you using so many nodes??")
	def selectList(self):
		return ",".join(self)+","
	def copy(self):
		return FeatureSet(set.copy(self))

hardlimit = 500 # how many tuples max should a query return?
reclimit = 100 # ... and what if that query is being used recursively in another query?
def buildquery(json,namer=None):
	if (namer is None):
		namer=FeatureSet()
	kind = next(iter(json.keys()))
	args = json[kind]
	if (kind=="syllables"):
		return f"SELECT word,word as {namer.newName()},1 as score FROM Words WHERE syllables={int(args[0])}"
	elif (kind=="rhyme"):
		if (type(args[0])==dict):
			newnames = namer.copy()
			subquery = buildquery(args[0],namer=newnames)
			newnames = FeatureSet(newnames-namer)
			namer.update(newnames)
			return f"""SELECT DISTINCT S1.word as word,{newnames.selectList()}S1.word as {namer.newName()},S2.score*RHYMES(S1.pronunciation,S3.pronunciation) as score
				   FROM (SELECT word,pronunciation,rhymekey FROM Words) S1 JOIN (SELECT * FROM ({subquery}) S LIMIT {reclimit}) S2 JOIN (SELECT word,pronunciation,rhymekey FROM Words) S3
				   ON S1.rhymekey=S3.rhymekey AND S2.word=S3.word
				   ORDER BY score DESC
				"""
		elif (type(args[0])==str):
			sanitize(args[0])
			return f"""SELECT word,word as {namer.newName()}, RHYMES(Words.pronunciation,S.pronunciation) as score
				   FROM Words JOIN (SELECT pronunciation,rhymekey FROM Words WHERE word="{args[0]}") S
				   ON Words.rhymekey=S.rhymekey
				   WHERE RHYMES(Words.pronunciation,S.pronunciation)>2
				   ORDER BY score DESC
				"""
	elif (kind=="alliteration"):
		if (type(args[0])==dict):
			newnames = namer.copy()
			subquery = buildquery(args[0],namer=newnames)
			newnames = FeatureSet(newnames-namer)
			namer.update(newnames)
			return f"""
					SELECT W.word,{newnames.selectList()}W.word as {namer.newName()},S.score as score
					FROM Words W JOIN ({subquery}) S JOIN Words W3 ON W3.word=S.word AND W3.alliterationkey=W.alliterationkey
					ORDER BY score DESC
				"""
		elif (type(args[0])==str):
			sanitize(args[0])
			return f"SELECT word,word as {namer.newName()},1 as score FROM Words WHERE alliterationkey=SUBSTRING(\"{args[0]}\",1,1)"
	elif(kind=="intersection"):
		if (type(args[0])==dict and type(args[1])==dict):
			newnames = namer.copy()
			subquery1 = buildquery(args[0],namer=newnames)
			subquery2 = buildquery(args[1],namer=newnames)
			newnames = FeatureSet(newnames-namer)
			namer.update(newnames)
			return f"""SELECT S1.word as word,{newnames.selectList()}S1.score+S2.score as score FROM ({subquery1}) S1 JOIN ({subquery2}) S2 ON S1.word=S2.word ORDER BY score DESC"""
	elif(kind=="synonym"):
		if (type(args[0])==str):
			sanitize(args[0])
			return f"SELECT word,word as {namer.newName()},1 as score FROM Synonyms WHERE synset IN (SELECT synset FROM Synonyms WHERE word=\"{args[0]}\") AND word<>\"{args[0]}\""
		elif (type(args[0])==dict):
			newnames = namer.copy()
			subquery = buildquery(args[0],namer=newnames)
			newnames = FeatureSet(newnames-namer)
			namer.update(newnames)
			return f"""
					SELECT DISTINCT Sy2.word as word,{newnames.selectList()}Sy2.word as {namer.newName()},S.score as score
					FROM Synonyms Sy1 JOIN ({subquery}) S JOIN Synonyms Sy2
					ON Sy1.word=S.word AND Sy2.synset=Sy1.synset
					ORDER BY S.score
				"""
	raise NotImplementedError("You did something unimplemented. Sorry.")

@app.route("/api/search",methods=["GET","POST"])
@form_has("data")
@uses_sql
def search(conn,cursor):
	try:
		query = buildquery(json.loads(request.form["data"]))
	except Exception as e: # could fail because: user intentionally broke form, user entered bad integer, user entered word with weird punctuation, etc.
		return str(e),400
	print(query)
	cursor.execute(query)
	columnnames = [x[0] for x in cursor.description]
	wordcolumn = columnnames.index("word")
	#return ",".join([x[0] for x in cursor.description])+"\n"+"\n".join(",".join(str(x) for x in word) for word in cursor),200
	return "<table><tr>"+" ".join(["<th>"+x+"</th>" for x in columnnames])+"</tr>"+"\n".join(["<tr>"+" ".join(["<th>"+str(x)+"</th>" for x in row])+"</tr>" for row in cursor])+"</table>"
