from flask import Flask, render_template, request, redirect, url_for, send_from_directory, make_response, send_file
import uuid
from database import db
from u_table import users_table as ut
import conf
from base64 import b64decode as decode
from io import BytesIO

app=Flask(__name__)
app.config['SECRET_KEY']=conf.key
app.config['CUSTOM_STATIC_PATH']=conf.static
dbase=db(conf.dbpath)
utable=ut(dbase,'users','un','pw','name')

def uid_by_sid(sid):
    uid=dbase.table('sessions').get_one('uid',sid=sid)
    if uid:return uid[0]
    return uid
def current_uid():return uid_by_sid(request.cookies.get('sid')) or -1
def usname(tb=None,uid=None):
    if uid is None:cuid=current_uid()
    if tb is None:return dbase.table('users').get_one('name',uid=uid)[0] if uid is not None else 'Unregistered'
    return tb.move('users').one('name',uid=uid)[0] if uid is not None else 'Войти'

def cusdata():
    sid=request.cookies.get('sid')
    if not sid:return None,None
    with dbase.table('sessions') as tb:
        uid=tb.one('uid',sid=sid)[0]
        #print(uid)
        uname=tb.move('users').one('name',uid=uid)[0]
    return uid,uname

def page(path,**kw):
    uid,nm=cusdata()
    nm=nm or 'Войти'
    return render_template(path,**kw,nm=nm,cuid=uid)
def prop_page(path,owner,**kw):return page(path,**kw,owner=owner)


# главная страница
@app.route(conf.route.home)
def index():
    with dbase.table('categories') as tb:
        ars=tb.all('cid','name')
    #print(page('home.html',ars=ars))
    return page('home.html',ars=ars)

@app.route(conf.route.ctg)
def category(cid):
    with dbase.table('categories') as tb:
        cnm=tb.one('name',cid=cid)
        #print(cnm,cid)
        if cnm:return page('category.html',ars=tb.move('articles').all('id','title',cid=cid),cnm=cnm[0],cid=cid)
    return page('error.html',title='404 error',article=['Category not found','мамкин хакер))'])

# форма для создания статьи
@app.route(conf.route.write_article,methods=['GET','POST'])
def write_article(cid):
    if request.method=='POST':
        title=request.form['title']
        content=request.form['content']
        #print(request.remote_addr)
        with dbase.table('articles') as tb:
            tb.insert(title=title,text=content,cid=cid,uid=current_uid())
            n=tb.one('last_insert_rowid()')[0]
            tb.move('files')
            for i in request.form['fids'].split(','):
                if i:tb.row(id=int(i)).update(aid=n)
        return redirect(url_for('index'))
    return page('write2.html',cid=cid) if dbase.table('categories').exists(cid=cid) else page('error.html',title='404 error',article=['Category not found','мамкин хакер'])

# страница статьи
@app.route(conf.route.article,methods=['GET','POST'])
def article(id):
    if request.method=='POST':
        txt=request.form['txt']
        if current_uid()>=0:
            with dbase.table('comments') as tb:tb.insert(aid=id,text=txt,uid=current_uid())
            return redirect(url_for('article',id=id))
        return redirect(url_for('login'))
    with dbase.table('articles') as tb:
        article=tb.one('title','text','uid',id=id)
        coms=[(*i,*tb.move('users').one('name',uid=i[0])) for i in tb.move('comments').all('uid','text','dt','cmid',aid=id)]
        fils=tb.move('files').all('id','name',aid=id)
    if article:
        title,article,uid=article
        return prop_page('article.html',owner=uid,title=title,article=article.split('\n'),cs=coms,id=id,fs=fils)
    return page('error.html',title='404 error',article=['Article not found','мамкин хакер))'])

@app.route(conf.route.delcom)
def delcom(aid,cmid):
    with dbase.table('comments') as tb:
        if current_uid()==(tb.one('uid',cmid=cmid) or [None])[0]:
            tb.row(cmid=cmid).delete()
    return redirect(url_for('article',id=aid))

@app.route(conf.route.delart)
def delart(id):
    with dbase.table('articles') as tb:
        if current_uid()==(tb.one('uid',id=id) or [None])[0]:
            tb.row(id=id).delete()
    return redirect(url_for('index'))

@app.route(conf.route.static)
def stat(file):return send_from_directory(app.config['CUSTOM_STATIC_PATH'],file)

@app.route('/author/')
def author():return page('error.html',title='Author',article=['Article is not written yet...','and never will be!','GET OUTTA HERE!!!'])

@app.route(conf.route.profile_by_uid)
@app.route(conf.route.my_profile)
def profile(uid=None):
    sid=request.cookies.get('sid')
    if sid and uid is None:return redirect(url_for('profile',uid=current_uid()))
    if uid is None:return redirect(url_for('login'))
    with dbase.table('users') as tb:
        un,nm=(tb.one('un','name',uid=uid) or (None,None))
        if un is None:return page('error.html',title='404 error',article=['Profile not found','мамкин хакер'])
        ars=tb.move('articles').all('id','title',uid=uid)
    return prop_page('profile.html',owner=uid,uname=un,name=nm,ars=ars)

@app.route(conf.route.login,methods=['GET','POST'])
def login():
    if request.method=='GET':
        if request.cookies.get('sid'):return redirect(url_for('logout'))
        return page('login.html')
    user=utable.auth(request,'un','pw','name','uid')
    if not user:return "Invalid username or password"
    nm,uid=user
    sid=str(uuid.uuid4())
    with dbase.table('sessions') as tb:tb.insert(sid=sid,uid=uid)
    rp=make_response(redirect(url_for('profile')))
    rp.set_cookie('sid', sid)
    return rp

@app.route(conf.route.register,methods=['GET','POST'])
def register():
    if request.method=='GET':return page('register.html')
    if utable.register(request,'un','pw','nm'):return redirect(url_for('login'))
    return redirect(url_for('register'))

@app.route(conf.route.logout)
def logout():
    sid=request.cookies.get('sid')
    rp=make_response(redirect(url_for('login')))
    if sid:
        rp.delete_cookie('sid')
        with dbase.table('sessions') as tb:tb.row(sid=sid).delete()
    return rp

def rec(nm,dt):
    with dbase.table('files') as tb:
        tb.insert(name=nm,data=dt)
        #print(tb.one('last_insert_rowid()')[0])

#@app.route(conf.route.fileform,methods=['GET','POST'])
def file_upl():
    if request.method=='GET':return page('file_upload_sample.html')
    #print(request.form['flist'])
    #print(request.form)
    #print('file names')
    #for i in request.form['flist'].split(','):
    #    if i:
    #        print(' ',request.form[f'file{i}name'])
    #        rec(request.form[f'file{i}name'],decode(request.form[f'file{i}content']))

    return redirect('/files/')

@app.route(conf.route.fileupl,methods=['POST'])
def filerx():
    with dbase.table('files') as tb:
        dt=request.files['file'].read()
        #print(len(dt),(15<<20))
        if len(dt)<=(15<<20):
            tb.insert(name=request.form['name'],data=dt)
            return str(tb.one('last_insert_rowid()')[0])
        return ''


@app.route(conf.route.filebyfid)
@app.route(conf.route.filebyfname)
def get_file(fid,fname=None):
    #if fname is None:
    #    with dbase.table('files') as tb:return redirect(url_for('get_file',fid=fid,fname=tb.one('name',id=fid)[0]))
    with dbase.table('files') as tb:
        #data=tb.one('data',id=fid,name=fname)[0]
        data,nm=(tb.one('data','name',id=fid)or(None,None))
        if data:return send_file(BytesIO(data),as_attachment=0,download_name=nm)
        else:return page('error.html',title='File not found',article=['wrong file id or name'])

@app.route('/track/<id>')
def track(id):return stat('p.png')

@app.route('/stp/')
def stp():
    exit()
    return ''

if __name__ == '__main__':app.run(debug=True,host='0.0.0.0',port=80)