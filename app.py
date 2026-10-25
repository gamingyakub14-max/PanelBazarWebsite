import os, sqlite3, secrets
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE, 'panel_bazar.db'))
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(
    BKASH_NUMBER=os.environ.get('BKASH_NUMBER', 'আপনার bKash নম্বর সেট করুন'),
    NAGAD_NUMBER=os.environ.get('NAGAD_NUMBER', 'আপনার Nagad নম্বর সেট করুন'),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE', '0') == '1',
    MAX_CONTENT_LENGTH=1024 * 1024,
)
PRODUCTS = [
 {'id':1,'name':'PHANTOM - AIMHACK','price':20,'tag':'NON ROOT','style':'purple','title':'PHANTOM','subtitle':'AIM PANEL'},
 {'id':2,'name':'BALA MODS - NON ROOT','price':25,'tag':'MAIN ID SAFE','style':'orange','title':'BALA MODS','subtitle':'ANDROID PANEL'},
 {'id':3,'name':'DRIP WIRE ANDROID EXTERNAL','price':30,'tag':'ANDROID','style':'blue','title':'DRIP WIRE','subtitle':'ANDROID EXTERNAL'},
 {'id':4,'name':'X-REG NON ROOT','price':18,'tag':'NON ROOT','style':'green','title':'X-REG','subtitle':'ANDROID PANEL'},
 {'id':5,'name':'DRIP CLIENT APK - NON ROOT','price':35,'tag':'NON ROOT','style':'purple','title':'DRIP CLIENT','subtitle':'NON ROOT'},
 {'id':6,'name':'PRIME MOD ANDROID PANEL','price':70,'tag':'FOR 2ND ID','style':'green','title':'PRIME MOD','subtitle':'MOBILE PANEL'},
 {'id':7,'name':'HG CLIENTS APK','price':40,'tag':'FOR 2ND ID','style':'orange','title':'HG CLIENTS','subtitle':'ANDROID PANEL'},
 {'id':8,'name':'X-REG PLAY','price':28,'tag':'ANDROID','style':'blue','title':'X-REG PLAY','subtitle':'SMOOTH + STABLE'},
]
def db():
    c=sqlite3.connect(DB_PATH, timeout=15); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c
def init_db():
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT NOT NULL UNIQUE COLLATE NOCASE,username TEXT NOT NULL UNIQUE COLLATE NOCASE,password_hash TEXT NOT NULL,balance INTEGER NOT NULL DEFAULT 0 CHECK(balance>=0),is_admin INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS deposits(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL REFERENCES users(id),method TEXT NOT NULL,amount INTEGER NOT NULL CHECK(amount>0),transaction_id TEXT NOT NULL UNIQUE COLLATE NOCASE,status TEXT NOT NULL DEFAULT 'pending',created_at TEXT NOT NULL,reviewed_at TEXT,reviewed_by INTEGER REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL REFERENCES users(id),product_id INTEGER NOT NULL,product_name TEXT NOT NULL,price INTEGER NOT NULL CHECK(price>0),status TEXT NOT NULL DEFAULT 'pending',created_at TEXT NOT NULL);
        ''')
        username=os.environ.get('ADMIN_USERNAME','').strip(); email=os.environ.get('ADMIN_EMAIL','').strip().lower(); password=os.environ.get('ADMIN_PASSWORD','')
        if username and email and password and not c.execute('SELECT id FROM users WHERE username=? OR email=?',(username,email)).fetchone():
            c.execute('INSERT INTO users(name,email,username,password_hash,balance,is_admin,created_at) VALUES(?,?,?,?,0,1,?)',('Administrator',email,username,generate_password_hash(password),datetime.utcnow().isoformat(timespec='seconds')))
def current_user():
    uid=session.get('user_id')
    if not uid: return None
    with db() as c: return c.execute('SELECT id,name,email,username,balance,is_admin,created_at FROM users WHERE id=?',(uid,)).fetchone()
def login_required(f):
    @wraps(f)
    def w(*a,**kw):
        if not current_user(): flash('আগে Login করুন।','error'); return redirect(url_for('login'))
        return f(*a,**kw)
    return w
def admin_required(f):
    @wraps(f)
    def w(*a,**kw):
        u=current_user()
        if not u or not u['is_admin']: abort(403)
        return f(*a,**kw)
    return w
def csrf_token():
    if '_csrf' not in session: session['_csrf']=secrets.token_urlsafe(24)
    return session['_csrf']
app.jinja_env.globals.update(csrf_token=csrf_token,current_user=current_user)
@app.before_request
def protect_post():
    if request.method=='POST':
        if not session.get('_csrf') or not request.form.get('_csrf') or not secrets.compare_digest(session['_csrf'],request.form.get('_csrf')): abort(400,'Security check failed. পেজ reload করে আবার চেষ্টা করুন।')
@app.after_request
def headers(r):
    r.headers['X-Content-Type-Options']='nosniff'; r.headers['X-Frame-Options']='DENY'; r.headers['Referrer-Policy']='strict-origin-when-cross-origin'; return r
@app.route('/')
def home(): return render_template('home.html',user=current_user(),products=PRODUCTS)
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form.get('name','').strip()[:80]; email=request.form.get('email','').strip().lower()[:150]; username=request.form.get('username','').strip()[:40]; pw=request.form.get('password',''); confirm=request.form.get('confirm','')
        if len(name)<2 or '@' not in email or len(username)<3 or not username.replace('_','').isalnum(): flash('নাম, সঠিক ইমেইল ও অক্ষর/সংখ্যার ইউজারনেম দিন।','error')
        elif len(pw)<8: flash('পাসওয়ার্ড কমপক্ষে ৮ অক্ষরের হতে হবে।','error')
        elif pw!=confirm: flash('দুটি পাসওয়ার্ড মিলছে না।','error')
        else:
            try:
                with db() as c: c.execute('INSERT INTO users(name,email,username,password_hash,created_at) VALUES(?,?,?,?,?)',(name,email,username,generate_password_hash(pw),datetime.utcnow().isoformat(timespec='seconds')))
                flash('অ্যাকাউন্ট তৈরি হয়েছে। এখন Login করুন।','success'); return redirect(url_for('login'))
            except sqlite3.IntegrityError: flash('এই ইমেইল বা ইউজারনেম আগে ব্যবহার করা হয়েছে।','error')
    return render_template('auth.html',mode='register')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        ident=request.form.get('identity','').strip(); pw=request.form.get('password','')
        with db() as c: u=c.execute('SELECT * FROM users WHERE email=? COLLATE NOCASE OR username=? COLLATE NOCASE',(ident,ident)).fetchone()
        if u and check_password_hash(u['password_hash'],pw):
            session.clear(); session['user_id']=u['id']; session['_csrf']=secrets.token_urlsafe(24); flash('সফলভাবে Login হয়েছে।','success'); return redirect(url_for('admin') if u['is_admin'] else url_for('home'))
        flash('ইমেইল/ইউজারনেম অথবা পাসওয়ার্ড ভুল।','error')
    return render_template('auth.html',mode='login')
@app.route('/logout',methods=['POST'])
@login_required
def logout(): session.clear(); flash('Logout হয়েছে।','success'); return redirect(url_for('home'))
@app.route('/account')
@login_required
def account():
    u=current_user()
    with db() as c:
        orders=c.execute('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC',(u['id'],)).fetchall(); deposits=c.execute('SELECT * FROM deposits WHERE user_id=? ORDER BY id DESC',(u['id'],)).fetchall(); spent=c.execute('SELECT COALESCE(SUM(price),0) n FROM orders WHERE user_id=?',(u['id'],)).fetchone()['n']
    return render_template('account.html',user=u,orders=orders,deposits=deposits,total_spent=spent)
@app.route('/buy/<int:pid>',methods=['POST'])
@login_required
def buy(pid):
    p=next((x for x in PRODUCTS if x['id']==pid),None)
    if not p: abort(404)
    u=current_user()
    with db() as c:
        cur=c.execute('UPDATE users SET balance=balance-? WHERE id=? AND balance>=?',(p['price'],u['id'],p['price']))
        if cur.rowcount!=1: flash('ব্যালেন্স পর্যাপ্ত নয়। আগে Add Fund করুন।','error'); return redirect(url_for('add_fund'))
        c.execute('INSERT INTO orders(user_id,product_id,product_name,price,created_at) VALUES(?,?,?,?,?)',(u['id'],p['id'],p['name'],p['price'],datetime.utcnow().isoformat(timespec='seconds')))
    flash('অর্ডার হয়েছে! প্যানেলের Key নিতে অ্যাডমিনের সাথে যোগাযোগ করুন।','success'); return redirect(url_for('account'))
@app.route('/add-fund',methods=['GET','POST'])
@login_required
def add_fund():
    if request.method=='POST':
        method=request.form.get('method',''); trx=request.form.get('transaction_id','').strip()[:100]
        try: amount=int(request.form.get('amount','0'))
        except ValueError: amount=0
        if method not in ('bKash personal','Nagad personal') or not 1<=amount<=1000000 or len(trx)<4: flash('সঠিক পেমেন্ট পদ্ধতি, টাকা ও Transaction ID দিন।','error')
        else:
            try:
                with db() as c: c.execute('INSERT INTO deposits(user_id,method,amount,transaction_id,created_at) VALUES(?,?,?,?,?)',(current_user()['id'],method,amount,trx,datetime.utcnow().isoformat(timespec='seconds')))
                flash('ডিপোজিট রিকোয়েস্ট জমা হয়েছে। Admin অনুমোদনের আগে ব্যালেন্স যোগ হবে না।','success'); return redirect(url_for('account'))
            except sqlite3.IntegrityError: flash('এই Transaction ID আগে জমা হয়েছে।','error')
    return render_template('add_fund.html')
@app.route('/admin')
@login_required
@admin_required
def admin():
    with db() as c:
        pending=c.execute("SELECT d.*,u.username,u.email FROM deposits d JOIN users u ON u.id=d.user_id WHERE d.status='pending' ORDER BY d.id").fetchall(); users=c.execute('SELECT id,name,email,username,balance,is_admin,created_at FROM users ORDER BY id DESC LIMIT 300').fetchall(); orders=c.execute('SELECT o.*,u.username FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC LIMIT 100').fetchall(); deposits=c.execute('SELECT d.*,u.username FROM deposits d JOIN users u ON u.id=d.user_id ORDER BY d.id DESC LIMIT 100').fetchall()
    return render_template('admin.html',pending=pending,users=users,orders=orders,deposits=deposits)
@app.route('/admin/deposit/<int:did>/<action>',methods=['POST'])
@login_required
@admin_required
def review_deposit(did,action):
    if action not in ('approve','reject'): abort(404)
    with db() as c:
        d=c.execute('SELECT * FROM deposits WHERE id=?',(did,)).fetchone()
        if not d or d['status']!='pending': flash('রিকোয়েস্ট আগে রিভিউ হয়েছে বা পাওয়া যায়নি।','error')
        elif action=='approve':
            cur=c.execute("UPDATE deposits SET status='approved',reviewed_at=?,reviewed_by=? WHERE id=? AND status='pending'",(datetime.utcnow().isoformat(timespec='seconds'),current_user()['id'],did))
            if cur.rowcount: c.execute('UPDATE users SET balance=balance+? WHERE id=?',(d['amount'],d['user_id'])); flash('ডিপোজিট অনুমোদিত; ব্যালেন্স যোগ হয়েছে।','success')
        else:
            c.execute("UPDATE deposits SET status='rejected',reviewed_at=?,reviewed_by=? WHERE id=? AND status='pending'",(datetime.utcnow().isoformat(timespec='seconds'),current_user()['id'],did)); flash('ডিপোজিট বাতিল হয়েছে।','success')
    return redirect(url_for('admin'))
@app.route('/admin/balance',methods=['POST'])
@login_required
@admin_required
def admin_balance():
    username=request.form.get('username','').strip(); action=request.form.get('action','add')
    try: amount=int(request.form.get('amount','0'))
    except ValueError: amount=0
    if not username or not 1<=amount<=1000000 or action not in ('add','subtract'): flash('সঠিক ইউজারনেম, পরিমাণ ও অ্যাকশন দিন।','error')
    else:
        delta=amount if action=='add' else -amount
        with db() as c: cur=c.execute('UPDATE users SET balance=balance+? WHERE username=? COLLATE NOCASE AND balance+?>=0 AND is_admin=0',(delta,username,delta))
        flash('ব্যালেন্স আপডেট হয়েছে।' if cur.rowcount else 'ইউজার পাওয়া যায়নি অথবা ব্যালেন্স যথেষ্ট নয়।','success' if cur.rowcount else 'error')
    return redirect(url_for('admin'))
@app.errorhandler(403)
def e403(_): return render_template('error.html',code=403,message='এই পেজ শুধু Admin ব্যবহার করতে পারবেন।'),403
@app.errorhandler(404)
def e404(_): return render_template('error.html',code=404,message='পেজটি পাওয়া যায়নি।'),404
init_db()
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT','5000')),debug=False)
