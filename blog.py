import os

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                autoescape = True)

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
        else:
            print ("[!] Error")
            print (subject)
            print(content)

        print (self.request)

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



app = webapp2.WSGIApplication([
                                ("/blog/newpost", NewPost),
                                ('/blog/([0-9]+)', PostPage),
                                ('/blog/?', BlogFront),
                            ], debug=True)















