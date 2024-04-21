from database import db
from hashlib import sha256
pwhash=lambda x:sha256(bytes(x,'utf16')).hexdigest()
class users_table:
	def __init__(s,dbase,tname,uname,pword,unmname,hsh=pwhash):
		s.db=dbase;s.tn=tname
		s.un=uname;s.pw=pword
		s.nm=unmname
		s.hsh=hsh
	def auth(s,rq,unn,pwn,*dt):
		un=rq.form[unn]
		pw=rq.form[pwn]
		with s.db.table(s.tn) as tb:return tb.one(*dt,**{s.un:un,s.pw:s.hsh(pw)})
	def register(s,rq,unn,pwn,nmn):
		un=rq.form[unn]
		pw=rq.form[pwn]
		nm=rq.form[nmn]
		with s.db.table(s.tn) as tb:
			if tb.one(s.un,**{s.un:un}):return False
			tb.insert(**{s.un:un,s.pw:s.hsh(pw),s.nm:nm})
		return True
	