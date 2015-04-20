import webapp2
import cgi
import string
import codecs

def escape_html(s):
    return cgi.escape(s, quote = True)

def rot13(s):
    return codecs.encode(s, 'rot_13')

form = """
<!DOCTYPE html>

<html>
  <head>
    <title>Unit 2 Rot 13</title>
  </head>

  <body>
    <h2>Enter some text to ROT13:</h2>
    <form method="post">
      <textarea name="text"
                style="height: 100px; width: 400px;">%(txt)s</textarea>
      <br>
      <input type="submit">
    </form>
     </body>

</html>
"""

class rot13MainPage(webapp2.RequestHandler):
    def write_form(self, txt=""):
        self.response.out.write(form %{"txt": escape_html(txt)})

    def get(self):
        self.write_form()

    def post(self):
        user_text = self.request.get('text')
        self.write_form(rot13(user_text))
