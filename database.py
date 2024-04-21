import sqlite3

class selector:
	def __init__(s,tbl,/,**kw):s.tbl,s.kw=tbl,kw
	def update(s,/,**kw):
		s.tbl.c.execute(f'UPDATE {s.tbl.name} SET '+" ".join(f"{i}=?" for i in kw)+' WHERE '+' AND '.join(f'{i}=?' for i in s.kw),(*kw.values(),*s.kw.values()))
	def delete(s):
		s.tbl.c.execute(f'DELETE FROM {s.tbl.name} WHERE '+' AND '.join(f'{i}=?' for i in s.kw),(*s.kw.values(),))

class table:
	def __init__(s,/,conn,name):
		s.name,s.conn,s.c=name,conn,conn.cursor()
	def __enter__(s):return s
	def __exit__(s,tp,val,tb):
		s.conn.commit()
		s.conn.close()
	def row(s,/,**kw):return selector(s,**kw)
	def insert(s,/,**kw):
		s.c.execute(f'INSERT INTO {s.name} ({", ".join(kw.keys())}) VALUES ({", ".join("?"*len(kw))})',tuple(kw.values()))
	def select(s,/,*a,**kw):
		if not kw:s.c.execute(f'SELECT {",".join(a)} FROM {s.name}')
		else:s.c.execute(f'SELECT {",".join(a)} FROM {s.name} WHERE '+' AND '.join(f'{i}=?' for i in kw),tuple(kw.values()))
	def one(s,/,*a,**kw):
		if a:s.select(*a,**kw)
		return s.c.fetchone()
	def all(s,/,*a,**kw):
		if a:s.select(*a,**kw)
		return s.c.fetchall()
	def get_one(s,/,*a,**kw):
		if a:s.select(*a,**kw)
		r=s.c.fetchone()
		s.__exit__(0,0,0)
		return r
	def get_all(s,/,*a,**kw):
		if a:s.select(*a,**kw)
		r=s.c.fetchall()
		s.__exit__(0,0,0)
		return r
	def move(s,new):
		s.name=new
		return s
	def exists(s,**kw):
		return s.get_one('*',**kw) is not None

class db:
	def __init__(self, path):
		self.p=path
	def table(s,name):
		#print(s.p)
		conn=sqlite3.connect(s.p)
		return table(conn,name)