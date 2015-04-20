import os
import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.dirname(__file__)
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

class PostEntry(db.Model):
    title = db.StringProperty(required = True)
    text = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

    def render(self):
        return self.text.replace('\n', '<br>')

def blog_key():
    return db.Key.from_path('blogs')

class BlogIndexPage(Handler):
    def render_front(self):
        posts = db.GqlQuery("SELECT * FROM PostEntry ORDER BY created DESC")
        self.render("index.html", posts=posts)

    def get(self):
        self.render_front()

class PostPage(Handler):
    def get(self, post_id):
        post = PostEntry.get_by_id(int(post_id))

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post)

class BlogNewPostPage(Handler):
    def render_front(self, title="", text="", error=""):
        self.render("new.html", title=title, text=text, error = error)

    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("subject")
        text = self.request.get("content")

        if title and text:
            a = PostEntry(title = title, text = text) # automatically a newkey is assigned
            a.put()
            self.redirect("/unit3/%s" % str(a.key().id())) # send the key id across

        else:
            error = "we need both a title and some blog-text!"
            self.render_front(title, text, error)
