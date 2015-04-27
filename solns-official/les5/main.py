import  os
import  re
import  sys
import urllib2
from xml.dom import minidom
from  string import letters
import  webapp2
import  jinja2
from  google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"
def gmap_img(points):
    markers = '&'.join('markers=%s,%s' % (p.lat, p.lon) for p in points)
    return GMAPS_URL + markers

IP_URL  = "http://api.hostip.info/?ip="
def get_coords(ip):
    ip ="12.215.42.19"
    url = IP_URL + ip
    content = None
    try:
        content = urllib2.urlopen(url).read()
    except urllib2.URLError:
        return
    if content:
        d = minidom.parseString(content)
        coords = d.getElementsByTagName("gml:coordinates")
        if coords and coords[0].childNodes[0].nodeValue:
            lon, lat = coords[0].childNodes[0].nodeValue.split(',')
            return db.GeoPt(lat, lon) #geopt is appengines way to store lattitide and longitude

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class Art(db.Model):
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    coords = db.GeoPtProperty()

class MainPage(Handler):
    def render_front(self, title="", art="", error=""):
        arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC LIMIT 10")
        arts = list(arts) # prevent running of multiple queries
        # find if any art has coords
        points = []
        for a in arts:
            if a.coords:
                points.append(a.coords)
        # if there is any arts with coords then make a image url
        img_url = None
        if points:
            img_url = gmap_img(points)
        self.render("front.html", title=title, art=art, error = error, arts=arts, img_url = img_url)

    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")

        if title and art:
            a = Art(title = title, art = art)
            """lookup the user's coordinates from their IP
            if we have coordinates, add them to the art
            if we go to http://api.hostip.info/?ip=12.215.42.19
            they'll return some XML with location data:
            """
            coords = get_coords(self.request.remote_addr)
            if coords:
                a.coords = coords
            # if we have coords add to art
            a.put() # store the new piece of art to our database
            self.redirect("/")

        else:
            error = "we need both a title and some artwork!"
            self.render_front(title, art, error)

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)
