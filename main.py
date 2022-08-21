from flask import Flask,render_template,request,session,redirect,flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail
import math
import json
import os

with open('config.json','r') as c:
    params=json.load(c)["params"]

local_server=True

app = Flask(__name__)
app.secret_key = 'SECRET-KEY'#secrate key for login
app.config['UPLOAD_FOLDER']=params['upload_location']
# sending mail
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT="465",
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail_username"],
    MAIL_PASSWORD=params["gmail_password"]
)
mail=Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]
db = SQLAlchemy(app)



class Contacts(db.Model):
    '''
    sno,name,email,phone_number,messge,date 
    '''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20),  nullable=False)
    phone_number = db.Column(db.String(12), unique=True, nullable=False)
    message= db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12),  nullable=True)
class Posts(db.Model):
    '''
    sno,title,slug,content,img_file,date 
    '''
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21),  nullable=False)
    content = db.Column(db.String(12), nullable=False)
    tagline = db.Column(db.String(12), nullable=False)
    img_file=db.Column(db.String(12),  nullable=True)
    date = db.Column(db.String(12),  nullable=True)


#home end point
@app.route('/')
def home():
    #pagination control next and prev button
    posts=Posts.query.filter_by().all()
    #[0:params['no_of_posts']]
    last=math.ceil(len(posts)/int(params['no_of_posts']))
    page=request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]
    #first page logic
    if(page==1):
        prev="#"
        next="/?page="+str(page+1)
    elif(page==last):
        prev="/?page="+str(page-1)
        next="#"
    else:
        prev="/?page="+str(page-1)
        next="/?page="+str(page+1)

    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)


#about end point
@app.route('/about')
def about():
    return render_template('about.html',params=params)


#dashboard end point
@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):  #checck user login or not
            posts=Posts.query.all()
            return render_template('dashboard.html',params=params,posts=posts)
    if request.method =='POST':
        username=request.form.get('uname')
        userpass=request.form.get('pass')
        if (username==params['admin_user'] and userpass==params['admin_password']):
            '''session variable set'''
            session['user']=username
            posts=Posts.query.all()
            flash("successfully login","success")
            return render_template('dashboard.html',params=params,posts=posts)
        flash("Please enter valid username and password","danger")
    return render_template('login.html',params=params)




# edit post end point
@app.route('/edit/<string:sno>',methods=['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):  #checck user login or not
        if request.method=='POST':
            box_title=request.form.get('title')
            tagline=request.form.get('tagline')
            slug=request.form.get('slug')
            content=request.form.get('content')
            img_file=request.form.get('img_file')
            date=datetime.now()
            #this if for add new post
            if sno=='0':
                post=Posts(title=box_title,slug=slug,content=content,tagline=tagline,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
                flash("Successfully add your new post","success")
                return redirect('/dashboard')
            #else use edit old post
            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=box_title
                post.tagline=tagline
                post.slug=slug
                post.content=content
                post.img_file=img_file
                post.date=date
                db.session.commit()
                flash("Successfully edit your post","success")
                # return redirect('/edit/'+sno)
                return redirect('/dashboard')
        post=Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post,sno=sno)


#delete post end point 
@app.route('/delete/<string:sno>',methods=['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):  #checck user login or not
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        flash("Successfully delete your post","success")
    return redirect('/dashboard')


#fileuploader end point
@app.route('/uploader',methods=['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):  #checck user login or not
        if request.method=='POST':
            f=request.files['file1']
            try:
                f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
                flash("Successfully upload your file","success")
                return redirect('/dashboard')
            except:
                flash("failed!! please try after some times","danger")
                return redirect('/dashboard')


#logout end point
@app.route('/logout')
def logout():
    session.pop('user')
    flash("Logout !! if you login please enter your username and password","success")
    return redirect('/dashboard')


@app.route("/post/<string:post_slug>",methods=['GET'])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)



@app.route('/contact',methods=['GET','POST'])
def contact():
    if(request.method=='POST'):
        ''' add entry to the database'''
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')
        '''
        add data base all data when post request send 
        '''
        entry=Contacts(name=name,phone_number=phone,message=message,email=email,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        try:
            mail.send_message('new message from '+ name,
            sender=email,
            recipients=[params['gmail_username']],
            body=message + " \n "+ phone
            )
            flash("Thanks for Submitting your details,we will back to contact you as soon as possible","success")
        except:
            flash("Somethin went wrong, Please try after Sometimes","danger")
    

    return render_template('contact.html',params=params)



if __name__ == '__main__':
    app.run(debug=True)