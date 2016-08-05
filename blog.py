import os
import re
import webapp2
import jinja2
import random
from google.appengine.ext import db
from string import letters
import hashlib
import hmac
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                autoescape = True)

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

def make_salt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()

    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')

def valid_username(username):
    return username and USER_RE.match(username)

def valid_password(password):
    return password and PASS_RE.match(password)

def valid_email(email):
    return not email or EMAIL_RE.match(email)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

secret = "2jd92hgkd9"
def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

class Handler (webapp2.RequestHandler):

    def write(self, *a, **kw):
        """
        calls response.out.write, no need to write out every time
        """
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        """
        Takes a template name and returns a string of that rendered template
        """
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        """
        Calls write on the string from render_str
        """
        self.write(self.render_str(template, **kw))

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))


    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/'%(name, cookie_val))

    def read_secure_cookie(self, name):
        # find the cookie in the request
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

class Post(db.Model):
    subject = db.StringProperty(required=True) #particular type
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

class NewPost(Handler):
    def get(self):
        #render form page
        self.render("newpost.html")

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            p = Post(subject=subject, content=content)
            #add to the DB
            p.put()

            self.redirect('/blog/%s' % str(p.key().id()))


class PostPage(Handler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id) )
        post = db.get(key)

        if not post:
            self.Error(404)

        self.render("permalink.html", post = post)

class BlogFront(Handler):
    def get(self):
        posts = greetings = Post.all().order('-created')
        self.render('front.html', posts = posts)

    def post(self):
        operation = self.request.get("operation")

        delete = operation == "delete"
        if delete:
            post_id = self.request.get("id")
            key = db.Key.from_path('Post', int(post_id) )
            db.delete(key)
            


class UpdatePost(Handler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id))
        post = db.get(key)

        error = ""
        self.render("updatepost.html", subject=post.subject,
                    content=post.content, error=error)
        
    def post(self, post_id):
        operation = self.request.get("operation")

        subject = self.request.get('subject')
        content = self.request.get('content')

        key = db.Key.from_path('Post', int(post_id))
        p = db.get(key)

        p.subject = self.request.get('subject')
        p.content = self.request.get('content')
        p.put()

        self.redirect('/blog/%s' % str(p.key().id()))

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')


def valid_username(username):
    return username and USER_RE.match(username)

def valid_password(password):
    return password and PASS_RE.match(password)

def valid_email(email):
    return not email or EMAIL_RE.match(email)

class User(db.Model):
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def by_name(cls, name):
        u = cls.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email=None):
        pw_hash = make_pw_hash(name, pw)
        return cls(name=name, pw_hash=pw_hash, email=email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u

    @classmethod
    def by_id(cls, uid):
        # get_by_id is a Datastore fxn
        return cls.get_by_id(uid)

class Register(Handler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        username = self.request.get("username")
        password_ = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        have_error = False
        params = dict(username=username, email=email)

        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True


        if not valid_password(password_):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password_ != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            user_exists = User.by_name(username)
            if user_exists:
                msg = 'That user already exists.'
                self.render('signup-form.html', error_username=msg)
            else:
                u = User.register(username, password_, email)
                u.put()

                self.login(u)
                self.redirect("/blog")

class Login(Handler):
    def get(self):
        self.render("login-form.html")

    def post(self):
        username = self.request.get("username")
        password_ = self.request.get("password")

        user_exists = User.login(username, password_)

        if user_exists:
            self.login(user_exists)
            self.redirect("/blog")
        else:
            msg = "Invalid Login"
            self.render('login-form.html', error=msg)

class Logout(Handler):
    def get(self):
        self.logout()
        self.redirect("/blog")

app = webapp2.WSGIApplication([
                                ("/blog/newpost", NewPost),
                                ('/blog/([0-9]+)', PostPage),
                                ('/blog/?', BlogFront),
                                ('/blog/([0-9]+)/updatepost', UpdatePost),
                                ('/signup', Register),
                                ('/login', Login),
                                ('/logout', Logout)
                                
                            ], debug=True)















