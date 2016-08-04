import os
import re
import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                autoescape = True)

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
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        """
        Calls write on the string from render_str
        """
        self.write(self.render_str(template, **kw))

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
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
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


class Register(Handler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        username = self.request.get("username")
        password_ = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        have_error = False
        params = dict(username=self.username, email=self.email)

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
                u = User.register(self.username, self.password, self.email)
                u.put()

                self.login(u)
                self.redirect("/blog")





app = webapp2.WSGIApplication([
                                ("/blog/newpost", NewPost),
                                ('/blog/([0-9]+)', PostPage),
                                ('/blog/?', BlogFront),
                                ('/blog/([0-9]+)/updatepost', UpdatePost),
                                ('/signup', Register)
                                
                            ], debug=True)















