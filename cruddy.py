from __future__ import with_statement
import subprocess
import sys
import os
import sqlite3
from google.protobuf.message import Message
from google.protobuf.descriptor import FieldDescriptor
from flask import Flask, render_template, request, redirect
from contextlib import closing

PROTO_FILE_SUFFIX = ".proto"
PYTHON_FILE_SUFFIX = ".py"
HTML_FILE_SUFFIX = ".html"

PYTHON_GENERATED_SUFFIX = "_pb2"
PROTO_TYPE_PREFIX = "TYPE_"

class Cruddy:
    source_dir = "protos"
    destination_dir = "objects"
    html_dir = "templates"
    static_dir = "static"

    schema_file = "schema.sql"

    # configuration
    database = 'storage.db'
    DEBUG = True
    SECRET_KEY = 'some key'
    USERNAME = 'admin'
    PASSWORD = 'default'

    def __init__(self):
        self.type_hash = {}
        self.generated_names = []
        self.app = Flask(__name__)


    ''' Returns a database connection object. '''
    def connect_db(self):
        return sqlite3.connect(self.database)


    def init_db(self):
        with closing(self.connect_db()) as db:
            with self.app.open_resource(self.schema_file) as f:
                db.cursor().executescript(f.read())
            db.commit()
        self.register_db_connections()


    def register_db_connections(self):
        def before_request():
            self.db = self.connect_db()
        def after_request(response):
            self.db.close()
            return response
        self.app.before_request(before_request)
        self.app.after_request(after_request)


    ''' Verifies the structure of the current working directory to make sure we have everything we need. '''
    def verify_structure(self):
        # Make sure the source directory exists and has protos in it.
        files = os.listdir(".")
        if self.source_dir not in files:
            raise Exception("Couldn't find source directory %s" % self.source_dir)
        else:
            protos = os.listdir(self.source_dir)
            for proto in protos:
                if proto.endswith(PROTO_FILE_SUFFIX):
                    break
            else:
                raise Exception("Found no .proto files in source directory %s" % self.source_dir)

        # Make sure the destination and HTML dirs exist.
        self.ensure_dir(self.destination_dir, files)
        self.ensure_dir(self.html_dir, files)


    ''' Ensures that a given directory exists in the current working directory. '''
    def ensure_dir(self, dirname, files):
        if dirname not in files:
            os.mkdir(dirname)


    ''' Generates the Protocol Buffer objects from the .proto files in the source directory. Assumes everything is there and in working order. '''
    def generate_protos(self):
        generated = []
        for proto in os.listdir(self.source_dir):
            try:
                subprocess.check_output(["protoc", "-I=%s" % self.source_dir, "--python_out=%s" % self.destination_dir, "%s/%s" % (self.source_dir, proto)]);
                object_name = proto[:len(PROTO_FILE_SUFFIX)]
                generated.append(object_name)
            except Exception as ex:
                sys.exit()

        return generated


    ''' Imports the given list as a series of objects to be brought into the current workspace. '''
    def import_proto(self, proto_objects):
        sys.path.append(self.destination_dir)
        object_names = map(lambda name: name + PYTHON_GENERATED_SUFFIX, proto_objects)
        modules = map(__import__, object_names)
        objects = []
        for object_name in object_names:
            objects.append(getattr(sys.modules[object_name], object_name[:-len(PYTHON_GENERATED_SUFFIX)])())
        return objects


    ''' Clears the HTML page directory '''
    def clear_html_pages(self):
        html_files = os.listdir(self.html_dir)
        for html_file in html_files:
            path = os.path.join(self.html_dir, html_file)
            if os.path.isfile(path):
                os.unlink(path)


    def generate_list_page(self, object_):
        name = self.get_name(object_)
        output_file = open(os.path.join(self.html_dir, name.lower() + "_list" + HTML_FILE_SUFFIX), 'w')
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
        name = self.get_name(object_)
        output_file = open(os.path.join(self.html_dir, name.lower() + "_view" + HTML_FILE_SUFFIX), 'w')
        output_file.write('''
            {% extends "base.html" %}
            {% block body %}\n''')
        for field in self.get_proto_fields(object_):
            output_file.write('''<p>{{ entry.%s }} <span class="muted">%s</span></p>''' % (field.name, self.type_hash[field.type]))

        output_file.write('''
            {% endblock %}\n''')
        output_file.close()


    def generate_new_page(self, object_):
        name = self.get_name(object_)
        output_file = open(os.path.join(self.html_dir, name.lower() + "_new" + HTML_FILE_SUFFIX), 'w')

        output_file.write('''
            {% extends "base.html" %}
            {% block body %}\n''')
        output_file.write('''<form action="/%s/add/" method="POST">''' % name.lower())
        for field in self.get_proto_fields(object_):
            output_file.write('''<p>%s <input type="text" name="%s"></p>''' % (field.name, field.name.lower()))
        
        output_file.write('''
                <input type="submit" text="Submit">
            </form>
            {% endblock %}\n''')
        output_file.close()


    def generate_base_page(self):
        output_file = open(os.path.join(self.html_dir, "base" + HTML_FILE_SUFFIX), 'w')
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


    ''' Creates a hash of the ProtocolBuffer types we have available, for lookup. '''
    def build_type_hash(self):
        for field_type in dir(FieldDescriptor):
            if field_type.startswith(PROTO_TYPE_PREFIX):
                self.type_hash[getattr(FieldDescriptor, field_type)] = field_type[len(PROTO_TYPE_PREFIX):].lower()


    ''' Runs and builds the app! '''
    def build_app(self):
        self.build_type_hash()

        # At this point it's just a few method calls.
        self.verify_structure()

        # Generate the proto file objects and import them into the current workspace.
        self.generated_names = self.generate_protos()
        self.generated_objects = self.import_proto(self.generated_names)

        # Clear out any existing HTML descriptor pages and rebuild them. 
        self.clear_html_pages()
        self.generate_base_page()
        for generated_object in self.generated_objects:
            self.generate_list_page(generated_object)
            self.generate_view_page(generated_object)
            self.generate_new_page(generated_object)
            self.build_routing(generated_object)

        # Build a schema file and create a database for us to use.
        self.build_schema(self.generated_objects)
        self.init_db()

        return self.app


    ''' Generates a function that will return the listing for the specific object name '''
    def generate_list_routing(self, object_):
        def _function():
            fields = self.get_proto_fields(object_)
            object_name = self.get_name(object_).lower()
            cur = self.db.execute('select %s from %s order by id desc' % (", ".join(map(lambda field: field.name.lower(), fields)), object_name))
            entries = []
            for row in cur.fetchall():
                entry = {}
                for index in range(len(row)):
                    entry[fields[index]] = row[index]
                entries.append(entry)
            return render_template(object_name + "_list" + HTML_FILE_SUFFIX, title=object_name, entries=entries)
        return _function


    ''' Generates a function that will return the rendering for the specific object name '''
    def generate_view_routing(self, object_):
        def _function(**kwargs):
            fields = self.get_proto_fields(object_)
            object_name = self.get_name(object_).lower()
            sql = 'select %s from %s where id = %s' % (", ".join(map(lambda field: field.name.lower(), fields)), object_name, kwargs['id'])
            cur = self.db.execute('select * from person')
            args = {}
            args["entry"] = cur.fetchall()[0]
            args["title"] = self.get_name(object_)
            return render_template(self.get_name(object_).lower() + "_view" + HTML_FILE_SUFFIX, **args)
        return _function


    ''' Generates a function that will return the rendering for the new-object form for the specific object name. '''
    def generate_new_routing(self, object_):
        def _function():
            return render_template(self.get_name(object_).lower() + "_new" + HTML_FILE_SUFFIX, title="New" + self.get_name(object_))
        return _function


    ''' Generates a function that will add a specified object to the database. '''
    def generate_add_routing(self, object_):
        def _function():
            fields = self.get_proto_fields(object_)
            sql = "insert into %s (%s) values (%s)" % (self.get_name(object_).lower(), ", ".join(map(lambda field: field.name.lower(), fields)), ", ".join(map(lambda field: "?", fields)))
            self.db.execute(sql, map(lambda field: request.form[field.name], fields))
            self.db.commit()

            return redirect('/%s/%s/' % (self.get_name(object_).lower(), request.form['id']))
        return _function


    ''' Builds the URL routings from the objects we have. '''
    def build_routing(self, object_):
        lower_name = self.get_name(object_).lower()
        self.app.add_url_rule('/%s/' % lower_name, "%s_list" % lower_name, self.generate_list_routing(object_)) # List
        self.app.add_url_rule('/%s/<id>/' % lower_name, "%s_view" % lower_name, self.generate_view_routing(object_)) # View
        self.app.add_url_rule('/%s/new/' % lower_name, "%s_new" % lower_name, self.generate_new_routing(object_)) # New
        self.app.add_url_rule('/%s/add/' % lower_name, "%s_add" % lower_name, self.generate_add_routing(object_), methods=["POST"]) # Add


    ''' Returns a list of the fields on an object generated by Protocol Buffers. '''
    def get_proto_fields(self, object_):
        return object_.DESCRIPTOR.fields


    ''' Returns the name of the type object '''
    def get_name(self, object_):
        return object_.__class__.__name__


    ''' Builds and outputs a schema file for the list of objects given. '''
    def build_schema(self, objects):
        output_file = open(self.schema_file, 'w')

        for object_ in objects:
            name = object_.__class__.__name__.lower()
            output_file.write("drop table if exists %s;\ncreate table %s (\n" % (name, name))
            column_descriptors = []
            for field in self.get_proto_fields(object_):
                column_name = field.name
                column_type = self.type_hash[field.type].replace("int32", "integer")
                if field.name is "id":
                    column_type += " primary key autoincrement"
                column_descriptors.append("  %s %s" % (column_name, column_type))
            output_file.write(",\n".join(column_descriptors))
            output_file.write(");")
        output_file.close()