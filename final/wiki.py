import os
import re
from string import letters
import random
import hashlib
import hmac
import webapp2
import jinja2
import logging

from google.appengine.api import memcache
from google.appengine.ext import db

SECRET = 'imsosecret'

import hmac
def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

def wiki_key(name = 'default'):
    return db.Key.from_path('wiki', name)

pattern = r"/?([a-zA-Z0-9_-]*)/?"
def stripPageName(page_name):
    match = re.search(pattern, page_name)
    if match is None:
        return ""
    return match.group(1)

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid)

    @classmethod
    def by_name(cls, name):
        # get returns the first result or None
        u = db.GqlQuery("select * from User where name=:1 limit 1", name).get()
        if u:
            return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(    name = name,
                        pw_hash = pw_hash,
                        email = email)

class WikiEntry(db.Model):
    name = db.StringProperty(required = True)
    text = db.TextProperty(required = True)

def wikiByName(page_name, update=False):
    if page_name=="": page_name="index"
    r = memcache.get(page_name)
    if r is None or update:
        if page_name == "index" and not update:
            # just for the first time
            stringy = r"""<h1>Welcome to Final!</h1>
                    <p>We are going to build a wiki..</p>"""
            memcache.set(page_name, stringy)
            w = WikiEntry(name = page_name, text = stringy, key_name= page_name) # automatically a newkey is assigned
            w.put()
            return stringy
        # get returns the first result or None
        logging.error("DB QUERY")
        #w = db.GqlQuery('SELECT * WHERE ANCESTOR IS :1 AND name = :2', wiki_key(),page_name).get()
        w = WikiEntry.get_by_key_name(page_name)
        if w:
            logging.error("FOUND DB-TEXT: " + w.text)
            r = w.text
            memcache.set(page_name, r)
    return r

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class SignupCookiePageFinal(BaseHandler):
    def get(self):
        self.render("signupForm.html")

    def post(self):
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username = username,
                      email = email)

        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signupForm.html', **params)
        else: # user, password is valid
            #make sure the user doesn't already exist
            u = User.by_name(username)
            if u:
                msg = 'That user already exists.'
                self.render('signupForm.html', error_username = msg)
            else:
                u = User.register(username, password, email)
                u.put()
                new_cookie_val = make_secure_val(str(u.key().id()))
                self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % str(new_cookie_val))
                self.redirect('/wiki')

class LoginPageFinal(BaseHandler):
    def render_front(self, username="", error=""):
        self.render('login-form.html', username=username, error=error)

    def get(self):
        self.render_front()

    def post(self):
        have_error = True
        username = self.request.get('username')
        password = self.request.get('password')
        u = User.by_name(str(username))
        if u is not None and valid_pw(username, password, str(u.pw_hash)):
            have_error = False
        if have_error:
            self.render_front(username, "Invalid login")
        else:
            new_cookie_val = make_secure_val(str(u.key().id()))
            self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % str(new_cookie_val))
            self.redirect('/wiki')

class LogoutPageFinal(BaseHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        self.redirect('/wiki')

class WikiPageFinal(BaseHandler):
    def get(self, pagename=""):
        pagename = stripPageName(pagename)
        if pagename=="": pagename="index"
        cookie_val = self.request.cookies.get("user_id")
        uid = cookie_val and check_secure_val(cookie_val)
        user = uid and User.by_id(int(uid))
        if user:
            # if the page exists show it, if not redirect to _edit/[page]
            wikiText = wikiByName(pagename)
            if pagename=="index": pagename=""
            if wikiText:
                self.render('index.html', pagename = pagename, text=wikiText, editable=True, username=user.name)
            else:
                self.redirect('/wiki/_edit/' + pagename)
        else:
            # show without the possibility to edit
            wikiText = wikiByName(pagename)
            if wikiText:
                self.render('index.html', pagename = pagename, text=wikiText)
            else:
                self.render('index.html', error = "The wiki you requested doesnt exist!")

class EditPageFinal(BaseHandler):
    def render_front(self, text="", error="", username="", editable=False, pagename=""):
        self.render("edit.html", text=text, pagename=pagename, username=username, error="", editable=editable)

    def get(self, pagename=""):
        pagename = stripPageName(pagename)
        cookie_val = self.request.cookies.get("user_id")
        uid = cookie_val and check_secure_val(cookie_val)
        user = uid and User.by_id(int(uid))
        error = ""
        if user:
            editable = True
        else:
            error="You are not authorised to edit"
        wikiText = wikiByName(pagename)
        if wikiText is None:
            wikiText = ""
        self.render_front(text=wikiText, pagename=pagename, editable=editable, error=error, username=user.name)


    def post(self, pagename=""):
        pagename = stripPageName(pagename)
        text = self.request.get("content")
        logging.error("POST PAGENAME: " + pagename)
        if text:
            if pagename=="": pagename="index"
            w = WikiEntry(name = pagename, text = text, key_name= pagename) # automatically a newkey is assigned
            w.put()
            wikiByName(pagename, update=True)
            if pagename=="index": pagename=""
            self.redirect("/wiki/" + str(pagename))

        else:
            error = "we need some wiki-text!"
            self.render_front(error=error, editable=True)
