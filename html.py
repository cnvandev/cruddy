import os
from utilities import get_proto_fields, get_name, source_dir, destination_dir, html_dir, static_dir, PROTO_FILE_SUFFIX, PYTHON_FILE_SUFFIX, HTML_FILE_SUFFIX, PYTHON_GENERATED_SUFFIX, PROTO_TYPE_PREFIX

class HTMLGenerator:

    def __init__(self, cruddy):
        self.cruddy = cruddy
        self.clear_html_pages()
        self.generate_base_page()
        for generated_object in cruddy.get_objects():
            self.generate_list_page(generated_object)
            self.generate_view_page(generated_object)
            self.generate_new_page(generated_object)


    ''' Clears the HTML page directory '''
    def clear_html_pages(self):
        html_files = os.listdir(html_dir)
        for html_file in html_files:
            path = os.path.join(html_dir, html_file)
            if os.path.isfile(path):
                os.unlink(path)


    def generate_list_page(self, object_):
        name = get_name(object_)
        output_file = open(os.path.join(html_dir, name.lower() + "_list" + HTML_FILE_SUFFIX), 'w')
        output_file.write('''
            {% extends "base.html" %}
            {% block body %}
            {% for entry in entries %}
              <h2>{{ entry.name }}</h2>
            {% else %}''')
        output_file.write('''
              <em>Nothing found! Maybe you should <a href="/%s/new/">add a new one</a>?</em>\n''' % name.lower()) 
        output_file.write('''
            {% endfor %}
            {% endblock %}\n''')
        output_file.close()


    ''' Generates an HTML page for the object! '''
    def generate_view_page(self, object_):
        name = get_name(object_)
        output_file = open(os.path.join(html_dir, name.lower() + "_view" + HTML_FILE_SUFFIX), 'w')
        output_file.write('''
            {% extends "base.html" %}
            {% block body %}\n''')
        for field in get_proto_fields(object_):
            output_file.write('''<p>{{ entry.%s }} <span class="muted">%s</span></p>''' % (field.name, self.cruddy.get_type_hash()[field.type]))

        output_file.write('''
            {% endblock %}\n''')
        output_file.close()


    def generate_new_page(self, object_):
        name = get_name(object_)
        output_file = open(os.path.join(html_dir, name.lower() + "_new" + HTML_FILE_SUFFIX), 'w')

        output_file.write('''
            {% extends "base.html" %}
            {% block body %}\n''')
        output_file.write('''<form action="/%s/add/" method="POST">''' % name.lower())
        for field in get_proto_fields(object_):
            output_file.write('''<p>%s <input type="text" name="%s"></p>''' % (field.name, field.name.lower()))
        
        output_file.write('''
                <input type="submit" text="Submit">
            </form>
            {% endblock %}\n''')
        output_file.close()


    def generate_base_page(self):
        output_file = open(os.path.join(html_dir, "base" + HTML_FILE_SUFFIX), 'w')
        output_file.write(self.generate_base())
        output_file.close()


    def generate_base(self):
        return '''
        <html>
            <head>
                <title>{{ title }}</title>
                <link href="/static/css/bootstrap.min.css" rel="stylesheet">
                <style>
                  body {
                    padding-top: 60px; /* 60px to make the container go all the way to the bottom of the topbar */
                  }
                </style>
            </head>
            <body>

                <div class="navbar navbar-inverse navbar-fixed-top">
                  <div class="navbar-inner">
                    <div class="container">
                      <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                      </a>
                      <a class="brand" href="#">LOLapps</a>
                      <div class="nav-collapse collapse">
                        <ul class="nav">
                          <li class="active"><a href="#">Home</a></li>
                          <li><a href="#about">About</a></li>
                          <li><a href="#contact">Contact</a></li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="container">
                {% block body %}{% endblock %}
                </div>

                <script src="http://code.jquery.com/jquery-latest.js"></script>
                <script src="/static/js/bootstrap.min.js"></script>
            </body>
        </html>
        '''