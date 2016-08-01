import os

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates_folder')
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

app = webapp2.WSGIApplication([
                                ("/blog/newpost", NewPost),
                                ('/blog/([0-9]+)', PostPage),
                                ('/blog/?', BlogFront),
                            ], debug=True)















