import os
import re
from string import letters
import random
import hashlib
import hmac
import webapp2
import jinja2

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

class SignupCookiePage(BaseHandler):

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
                self.redirect('/blog/welcome')

class WelcomeCookiePage(BaseHandler):
    def get(self):
        cookie_val = self.request.cookies.get("user_id")
        uid = cookie_val and check_secure_val(cookie_val)
        user = uid and User.by_id(int(uid))
        if user:
            self.render('welcome.html', username = user.name)
        else:
            self.redirect('/blog/signup')

class LoginPage(BaseHandler):
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
            self.redirect('/blog/welcome')

class LogoutPage(BaseHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        self.redirect('/blog/signup')
