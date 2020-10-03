# -*- coding: utf-8 -*-
"""
Created on Wed May 13 13:27:41 2020

@author: Admin
"""

from couchbase.cluster import Cluster
from couchbase.cluster import PasswordAuthenticator
from couchbase import bucket
import os
from flask import Flask,redirect, url_for, render_template, flash,session, request
app = Flask(__name__)
app.secret_key = "you-will-never-guess"
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,BooleanField, TextAreaField
from wtforms.validators import DataRequired
import couchbase.subdocument as SD
from couchbase.bucket import Bucket
from datetime import timedelta, date
cb = Bucket('couchbase://localhost/Post_it',username='Administrator', password='keerthana')
app.permanent_session_lifetime=timedelta(days=2)
    
class SignUpForm(FlaskForm):
    emailid = StringField('EMAIL  ID:', validators=[DataRequired()])
    username = StringField('USERNAME: ', validators=[DataRequired()])
    password = PasswordField('PASSWORD:', validators=[DataRequired()])
    submit = SubmitField('SIGN IN')
    
class LoginForm(FlaskForm):
    username = StringField('USERNAME: ', validators=[DataRequired()])
    password = PasswordField('PASSWORD: ', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('LOGIN')
    
class PostForm(FlaskForm):
    post=TextAreaField('')
    submit=SubmitField('Post')
    
class LikeForm(FlaskForm): 
    submit=SubmitField('Like')
    

@app.route('/home',methods=['GET','POST'])
def home():  
    return render_template('home.html')

@app.route('/post',methods=['GET','POST'])
def post():
    form = PostForm()
    if "currentuser" in session:
        if form.validate_on_submit():
            author=session["currentuser"]
            p=form.post.data
            if p!="":
                res = cb.counter('counter',delta = 1).value
                pid='p'+str(res)
                dated=date.today()
                dated=str(dated)
                cb.insert(pid, {'post':p,'author':author,'type':'post','date':dated,'likes':0})  
            return redirect("posts") 
    else:
        return redirect("login")
    return render_template('post.html', title='Sign In', form=form) 
 
@app.route('/posts',methods=['GET','POST'])
def posts():
   poe=[]
   aut=[]
   datee=[]
   like=[]
   pid=[]
   res=cb.get('counter').value
   if res == 0:
       re = cb.get('nopost')
       r=re.value
       poe.append(r['post'])     
       return render_template('posts.html', title='Post',content=poe,name=session["currentuser"],n=res)
   else:
        i='p'
        p='0'
        t=0
        for j in range(res,0,-1):
            pe=int(p)+j
            po=i+str(pe)
            r = cb.get(po).value
            if r['post']!=None:
                pid.append(po)
                aut.append(r['author'])
                poe.append(r['post'])
                datee.append(r['date'])
                like.append(r['likes'])
                t=t+1
        if t==0:
            re = cb.get('nopost')
            r=re.value
            poe.append(r['post'])
            return render_template('posts.html', title='Post',content=poe,name=session["currentuser"],n=t)    
        else:
            return render_template('posts.html', title='Post',content=poe,name=session["currentuser"],n=t,author=aut,date=datee,likes=like,poid=pid)   
   return render_template('posts.html', title='Post')  
     

@app.route('/signup',methods=['GET','POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        e=form.emailid.data
        a=form.username.data
        b=form.password.data
        cb.insert(a, {'emailid':e,'username': a,'password':b,'type':'user'})  
        return redirect("login")
    return render_template('signup.html', title='Sign In', form=form)

@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        a=form.username.data
        b=form.password.data
        result = cb.get(a)
        r=result.value
        u=r['username']
        p=r['password']
        session["currentuser"]=u
        session.permanent=True
        if(p==b and u==a):  
            flash("Logged in successfully!","info")
            return redirect("posts")
        else:
            flash("INCORRECT PASSWORD","info")
            return render_template('login.html', title='Sign In', form=form)
    return render_template('login.html', title='Sign In', form=form)


@app.route("/logout")
def logout():
    if "currentuser" in session:
        session.pop("currentuser",None)
        flash("Logged out successfully!","info")
        return redirect("home")
    
@app.route("/like/<string:ids>",methods=['GET','POST'])
def like(ids):
        res=cb.mutate_in(ids,[ SD.counter("likes",1, create_parents= True)])
        return redirect(url_for('posts'))
    
@app.route("/delete/<string:ids>",methods=['GET','POST'])
def delete(ids):
        res=cb.mutate_in(ids,[SD.replace("post",None)])
        return redirect(url_for('myposts'))    
    
@app.route("/edit/<string:ids>",methods=['GET','POST'])
def edit(ids):
        form = PostForm()
        da=cb.get(ids).value
        form.post.data=da['post']
        if "currentuser" in session:
            if form.validate_on_submit():
                poo= request.form['post']
                if poo!="":
                    res=cb.mutate_in(ids,[SD.replace("post",poo)])  
                    return redirect(url_for('myposts')) 
        else:
            return redirect("login")
        return render_template('edit.html', title='Sign In', form=form)
    

    
@app.route("/myposts",methods=['GET','POST'])
def myposts():
    if "currentuser" in session:
        me=session["currentuser"]
        res=cb.get('counter').value
        i='p'
        p='0'
        mine=[]
        dd=[]
        l=[]
        flag=0;
        pid=[]
        for j in range(res,0,-1):
            pe=int(p)+j
            po=i+str(pe)
            res = cb.get(po)
            r=res.value
            if me==r['author'] and r['post']!=None:
                pid.append(po)
                flag=flag+1;
                mine.append(r['post'])
                dd.append(r['date'])
                l.append(r['likes'])
        if flag!=0:
                return render_template('myposts.html', title='Post',content=mine,name=session["currentuser"],n=flag,date=dd,like=l,poid=pid)
        else:
                msg=cb.get('noposts').value
                msg=msg['post']
                return render_template('myposts.html', title='Post',content=msg,name=session["currentuser"],n=flag)
    else:
        return redirect("login")   
    


if __name__ == "__main__":
    app.run()    