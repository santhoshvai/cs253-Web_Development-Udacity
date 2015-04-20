import os
import webapp2
import jinja2
from unit2.rot13 import rot13MainPage
from unit2.signup import SignupMainPage, WelcomePage
from unit3.blog import BlogIndexPage, BlogNewPostPage, PostPage

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainPage(Handler):
    def get(self):
        self.render("index.html")

app = webapp2.WSGIApplication([
    ('/', MainPage),
    # unit 2
    ('/unit2/rot13', rot13MainPage),
    ('/unit2/signup', SignupMainPage),
    ('/unit2/welcome', WelcomePage),
    # unit 3
    ('/unit3/?', BlogIndexPage),
    ('/unit3/newpost', BlogNewPostPage),
    ('/unit3/([0-9]+)', PostPage) # anything in () is sent as a parameter
], debug=True)
