import os
import webapp2
import jinja2
import json
from datetime import datetime
import logging

from google.appengine.api import memcache
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

    def as_dict(self):
        time_fmt = '%c'
        d = {'subject': self.title,
             'content': self.text,
             'created': self.created.strftime(time_fmt)}
        return d

    def createdTime(self):
        return self.created.strftime("%c")

def blog_key():
    return db.Key.from_path('blogs')

def postById(post_id):
    key = str(post_id)
    r = memcache.get(key)
    if r is None:
        post = PostEntry.get_by_id(int(post_id))
        memcache.set(key, (post, datetime.now()))
        aged = 0
    else:
        post, age = r
        aged = int((datetime.now() - age).total_seconds())
    return post, aged

# storing db queries in cache
def top_posts(update = False):
    key = 'top'
    r = memcache.get(key)
    if r is None or update:
        logging.error("DB QUERY")
        posts = db.GqlQuery("SELECT * FROM PostEntry ORDER BY created DESC")
        memcache.set(key, (posts, datetime.now()))
        aged = 0
    else:
        posts, age = r
        aged = int((datetime.now() - age).total_seconds())
    return posts, aged

lastQuery = datetime.now()

class BlogIndexPage(Handler):
    def render_front(self):
        #posts = db.GqlQuery("SELECT * FROM PostEntry ORDER BY created DESC")
        posts, since = top_posts()
        if self.request.url.endswith('.json'):
            json_txt = json.dumps([p.as_dict() for p in posts])
            self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
            self.write(json_txt)
        else:
            self.render("index.html", posts=posts, secs=since)

    def get(self):
        self.render_front()

class PostPage(Handler):
    def get(self, post_id):
        post, since = postById(post_id)
        if not post:
            self.error(404)
            return
        if self.request.url.endswith('.json'):
            json_txt = json.dumps(post.as_dict())
            self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
            self.write(json_txt)
        else:
            self.render("permalink.html", post = post, secs = since)

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
            #rerun the query and update the cache
            top_posts(True)
            self.redirect("/blog/%s" % str(a.key().id())) # send the key id across

        else:
            error = "we need both a title and some blog-text!"
            self.render_front(title, text, error)

class FlushPage(Handler):
    def get(self):
        memcache.flush_all()
        self.redirect("/blog")
