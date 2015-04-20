import webapp2
import cgi
import re
html = """
<!DOCTYPE html>

<html>
  <head>
    <title>Sign Up</title>
    <style type="text/css">
      .label {text-align: right}
      .error {color: red}
    </style>

  </head>

  <body>
    <h2>Signup</h2>
    <form method="post">
      <table>
        <tr>
          <td class="label">
            Username
          </td>
          <td>
            <input type="text" name="username" value="%(username)s">
          </td>
          <td class="error">
          %(err_username)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Password
          </td>
          <td>
            <input type="password" name="password" value="%(password)s">
          </td>
          <td class="error">
          %(err_password)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Verify Password
          </td>
          <td>
            <input type="password" name="verify" value="%(verify)s">
          </td>
          <td class="error">
          %(err_verify)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Email (optional)
          </td>
          <td>
            <input type="text" name="email" value="%(email)s">
          </td>
          <td class="error">
          %(err_email)s
          </td>
        </tr>
      </table>

      <input type="submit">
    </form>
  </body>

</html>
"""
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
MAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def valid_username(txt):
    return USER_RE.match(txt)

def valid_password(txt):
    return PASS_RE.match(txt)

def valid_mail(txt):
    return MAIL_RE.match(txt)

def valid_verify(txt1, txt2):
    return txt1 == txt2

def escape_html(s):
    return cgi.escape(s, quote = True)

class SignupMainPage(webapp2.RequestHandler):
    def write_form(self, username=None, password=None, verify=False, email=None, user_username=None, user_password=None, user_email=None):
        err_username = ""
        err_password = ""
        err_verify = ""
        err_email = ""

        if (username is not None):
            username = escape_html(user_username)
        else:
            username = ""
            if user_username is not None:
                err_username = "That's not a valid username"

        if (password is None):
            if user_password is not None:
                err_password = "That's not a valid password"

        if verify == False:
            if user_password is not None:
                err_verify = "Passwords dont match"

        if (email is not None):
            email = escape_html(user_email)
        else:
            email = ""
            if (user_email is not None and user_email != ""):
                err_email = "Thats not a valid email"

        self.response.out.write(html %{"username": username,
        "password" : "",
        "verify" : "",
        "email" : email,
        "err_username" : err_username,
        "err_password" : err_password,
        "err_verify" : err_verify,
        "err_email" : err_email})

    def get(self):
        self.write_form()

    def post(self):
        user_username = self.request.get('username')
        user_password = self.request.get('password')
        user_verify = self.request.get('verify')
        user_email = self.request.get('email')
        val_username = valid_username(user_username)
        val_password = valid_password(user_password)
        val_verify = valid_verify(user_password,user_verify)
        val_mail = valid_mail(user_email)
        if user_email != "":
            if(val_username and val_password and val_verify and val_mail):
                self.redirect('/unit2/welcome?username=%(username)s'%{"username": escape_html(user_username)})
            else:
                self.write_form(val_username, val_password, val_verify, val_mail, user_username, user_password, user_email)
        else:
            if(val_username and val_password and val_verify):
                self.redirect('/unit2/welcome?username=%(username)s'%{"username": escape_html(user_username)})
            else:
                self.write_form(val_username, val_password, val_verify, val_mail, user_username, user_password, user_email)

class WelcomePage(webapp2.RequestHandler):
    def get(self):
        user = self.request.get('username')
        self.response.out.write(r'<h1 style="color: blue">Welcome&#44; %(user)s&#33;</h1>'%{"user": user})
