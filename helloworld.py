import webapp2
html = """
<!DOCTYPE html>

<html>
  <head>
    <title>udacity-cs253 Santosh's implementation HOME</title>
  </head>

  <body>
    <h2>Hello, udacity!, created on 14 apr 2015, my own webdev 101</h2>
    <br>
    <a href="/unit2/rot13">HW 1.1 - rot13</a>
    <br>
    <a href="/unit2/signup">HW 1.2 - signup</a>
  </body>

</html>
"""
class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write(html)

app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
