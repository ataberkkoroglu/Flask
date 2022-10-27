from flask_mysqldb import MySQL
from flask import Flask,redirect,render_template,url_for,session,flash,request
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#Admission
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
           return f(*args, **kwargs)
        else:
            flash("Bu Sayfayı Görüntülemek İçin Lütfen Giriş Yapınız...","danger")
            return redirect(url_for("Login"))
    return decorated_function

#KayıtForm
class KayıtForm(Form):
  Name=StringField("Name",validators=[validators.DataRequired(message= "Write Your Name")])
  Surname=StringField("Surname",validators=[validators.DataRequired(message= "Write Your Surname")])
  E_mail=StringField("E-Mail Address",validators=[validators.Email(message="Your E-mail address Isn't Compatible")])
  username=StringField("Username",validators=[validators.DataRequired(message="Write Your Username"),validators.Length(min=4)])
  password=PasswordField("Password",validators=[validators.DataRequired(),validators.Length(min=6),validators.EqualTo("confirm" ,message="This Password Isn't Compatible Your Password")])
  confirm=PasswordField("Verify Your Password")

#LoginForm 
class GirişForm(Form):
    Username=StringField("Username",validators=[validators.DataRequired(message="Your username is wrong"),validators.Length(min=4)])
    password=PasswordField("Password",validators=[validators.DataRequired(message="Your Password is wrong."),validators.Length(min=6)])

#AddProject
class AddProject(Form):
    Title=StringField("Name Of Your Project",validators=[validators.data_required("Please Write Your Project's Title")])
    Text=TextAreaField("Content Of Your Project",validators=[validators.Length(min=1)])
    
app=Flask(__name__)
app.secret_key="ataberk"
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="ATABERK"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql=MySQL(app)

#home
@app.route("/")
def home():
    return render_template("home.html")

#about
@app.route("/about")
def about():
    return render_template("about.html")

#details
@app.route("/project/<string:id>")
@login_required
def Details(id):
    cursor=mysql.connection.cursor()
    result=cursor.execute("Select * From projects where id=%s",(id,))
    if result !=0:
      project=cursor.fetchone()
      return render_template("projects.html",project=project)
    else:
      return render_template("projects.html")

#register
@app.route("/register",methods=["GET","POST"])
def Register():
    record=KayıtForm(request.form)
    if request.method=="POST" and record.validate():
     name=record.Name.data
     surname=record.Surname.data
     e_mail=record.E_mail.data
     username=record.username.data
     password=sha256_crypt.encrypt(record.password.data)
     confirm=sha256_crypt.encrypt(record.confirm.data)
     cursor=mysql.connection.cursor()
     result2=cursor.execute("Select * From users where username=%s and Email=%s",(username,e_mail))

     if result2!=0:
        flash("This Username Has Already Been Existed.","danger")
        return redirect(url_for("Register"))
     elif result2==0:
      cursor.execute("Insert Into users(name,Surname,username,Email,password) Values(%s,%s,%s,%s,%s)",(name,surname,username,e_mail,password))
      mysql.connection.commit()
      sorgu=("Select * From users where username=%s and Email=%s")
      result=cursor.execute(sorgu,(username,e_mail))
      if result==0:
        flash("Your Process couldn't be realized.","danger")
        return redirect(url_for("Register"))
      elif result!=0:
        flash("Your Process could be realized succesfully.","success")
        return redirect(url_for("Login"))
    else:
       return render_template("register.html",record=record)

#Login
@app.route("/login",methods=["GET","POST"])
def Login():
    form=GirişForm(request.form)
    if request.method=="POST":
      username=form.Username.data
      password=form.password.data
      cursor=mysql.connection.cursor()
      sorgu=("Select * From users Where username=%s")
      result=cursor.execute(sorgu,(username,))
      if result!=0:
        cursor.execute("Select * From users Where username=%s ",(username,))
        data=cursor.fetchone()
        session["logged_in"]=True
        session["username"]=username
        real_password=data["password"]
        if sha256_crypt.verify(password,real_password):
             flash("Your Process could be realized succesfully.","success")
             return redirect(url_for("home"))
        else:
            flash("Please Check Your Informations","danger")
            return redirect(url_for("login"))
      elif result==0:
            flash("User Not Found","danger")
            return redirect(url_for("Register"))
      
    else:
        return render_template("login.html",form=form)

#Log Out
@app.route("/logout")
def Exit():
    session.clear()
    flash("Logged Out","success")
    return render_template("home.html")
    
#Searching Project
@app.route("/project",methods=["POST"])
def search():
  if request.method=="POST":
   keyword=request.form.get("keyword")
   cursor=mysql.connection.cursor()
   sorgu=("Select * From projects where Title like '%" + keyword +"%' ")
   result=cursor.execute(sorgu,)
   if result!=0:
    project=cursor.fetchall()
    return render_template("project.html",project=project)
   elif result==0:
    flash("Searching Projects hasn't Been Found.","warning")
    return redirect(url_for("project"))
 

#Projects
@app.route("/project")
def projects():
  cursor=mysql.connection.cursor()
  sorgu=("Select * From projects")
  result=cursor.execute(sorgu,)
  if result!=0:
    project=cursor.fetchall()
    return render_template("project.html",project=project)
  elif result==0:
    return render_template("project.html")

@app.route("/addproject",methods=["GET","POST"])
@login_required
def AddProjects():
  form=AddProject(request.form)
  if request.method=="POST" and form.validate():
    Title=form.Title.data
    Text=form.Text.data
    cursor=mysql.connection.cursor()
    sorgu=("Insert into projects(Title,Author,Content) Values(%s,%s,%s)")
    cursor.execute(sorgu,(Title,session["username"],Text))
    mysql.connection.commit()
    result=cursor.execute("Select * From projects where Title=%s",(Title,))
    if result!=0:
      flash("Your Process could be Realized Successfully","sucess")
      return redirect(url_for("dashboard"))
    elif result==0:
     flash("Your Process couldn't be Realized Successfully.","success")
     return redirect(url_for("AddProjects"))
  elif request.method=="GET":
     return render_template("AddProject.html",form=form)

#Dashboard
@app.route("/dashboard")
def dashboard():
  cursor=mysql.connection.cursor()
  cursor.execute("Select * From projects Where Author=%s",(session["username"],))
  project=cursor.fetchall()
  if project !=0:
   
   return render_template("dashboard.html",project=project)
  elif result==0:
    
    return render_template("dashboard.html")

#update a project
@app.route("/edit/<string:id>",methods=["GET","POST"])
def Update(id):
  form=AddProject(request.form)
  if request.method=="GET":
   cursor=mysql.connection.cursor()
   cursor.execute("Select * From projects where id=%s",(id,))
   result=cursor.fetchone()
   if result==0:
      flash("You don't have Competency or There is no such a project","danger")
      return redirect(url_for("dashboard"))

   elif result!=0:
      cursor.execute("Select * From projects where id=%s",(id,))
      Project=cursor.fetchone()
      
      form.Title.data=Project["Title"]
      form.Text.data=Project["Content"]
      return render_template("update.html",form=form)
      
  else:
    #Post Request
    
    cursor=mysql.connection.cursor()
    cursor.execute("Update projects set Title=%s,Content=%s Where id=%s",(form.Title.data, form.Text.data,id))
    mysql.connection.commit()
    cursor.execute("Select * From projects Where Title=%s and Content=%s",(form.Title.data,form.Text.data))
    result2=cursor.fetchone()
    if result2==0:
      flash("Your Process Couldn't Be Realized Successfully","danger")
      return redirect(url_for("update"))
    elif result2!=0:
      flash("Your Process Couldn't Be Realized Successfully","success")
      return redirect(url_for("dashboard"))
    
#Delete Project
@app.route("/delete/<string:id>")
@login_required
def delete(id):
 
  cursor=mysql.connection.cursor()
  cursor.execute("Select * From projects Where id=%s",(id,))
  result=cursor.fetchone()
  if result==0:
   flash("You don't have Competency or There is no such a project","danger")
   return redirect(url_for("dashboard"))

  elif result!=0:
   cursor.execute("Delete From projects Where id=%s",(id,))
   mysql.connection.commit()
   cursor.execute("Select * From projects Where id=%s",(id,))
   sonuc=cursor.fetchone()
   if sonuc==0:
    flash("Your Process Could Be Realized Successfully","success")
    return redirect(url_for("dashboard"))
   else:
    flash("Your Process Couldn't Be Realized Successfully","danger")
    return redirect(url_for("home"))
    
if __name__=='__main__':
    app.run(debug=True)