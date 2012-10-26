import subprocess
import sys
import os
from google.protobuf.message import Message
from google.protobuf.descriptor import FieldDescriptor
from flask import Flask, render_template, request, redirect
from utilities import get_proto_fields, get_name, source_dir, destination_dir, html_dir, static_dir, PROTO_FILE_SUFFIX, PYTHON_FILE_SUFFIX, HTML_FILE_SUFFIX, PYTHON_GENERATED_SUFFIX, PROTO_TYPE_PREFIX
from html import HTMLGenerator
from storage import DBStorage

class Cruddy:
    
    def __init__(self):
        self.type_hash = {}
        self.generated_names = []

        self.app = Flask(__name__)

        self.build_type_hash()

        # At this point it's just a few method calls.
        self.verify_structure()

        # Generate the proto file objects and import them into the current workspace.
        self.generated_names = self.generate_protos()
        self.generated_objects = self.import_proto(self.generated_names)

        self.db = DBStorage(self)
        self.html = HTMLGenerator(self)

        # Create the HTML routings.
        for generated_object in self.generated_objects:
            self.build_routing(generated_object)


    ''' Verifies the structure of the current working directory to make sure we have everything we need. '''
    def verify_structure(self):
        # Make sure the source directory exists and has protos in it.
        files = os.listdir(".")
        if source_dir not in files:
            raise Exception("Couldn't find source directory %s" % source_dir)
        else:
            protos = os.listdir(source_dir)
            for proto in protos:
                if proto.endswith(PROTO_FILE_SUFFIX):
                    break
            else:
                raise Exception("Found no .proto files in source directory %s" % source_dir)

        # Make sure the destination and HTML dirs exist.
        self.ensure_dir(destination_dir, files)
        self.ensure_dir(html_dir, files)


    ''' Ensures that a given directory exists in the current working directory. '''
    def ensure_dir(self, dirname, files):
        if dirname not in files:
            os.mkdir(dirname)


    ''' Generates the Protocol Buffer objects from the .proto files in the source directory. Assumes everything is there and in working order. '''
    def generate_protos(self):
        generated = []
        for proto in os.listdir(source_dir):
            try:
                subprocess.check_output(["protoc", "-I=%s" % source_dir, "--python_out=%s" % destination_dir, "%s/%s" % (source_dir, proto)]);
                object_name = proto[:len(PROTO_FILE_SUFFIX)]
                generated.append(object_name)
            except Exception as ex:
                sys.exit()

        return generated


    ''' Imports the given list as a series of objects to be brought into the current workspace. '''
    def import_proto(self, proto_objects):
        sys.path.append(destination_dir)
        object_names = map(lambda name: name + PYTHON_GENERATED_SUFFIX, proto_objects)
        modules = map(__import__, object_names)
        objects = []
        for object_name in object_names:
            objects.append(getattr(sys.modules[object_name], object_name[:-len(PYTHON_GENERATED_SUFFIX)])())
        return objects


    ''' Creates a hash of the ProtocolBuffer types we have available, for lookup. '''
    def build_type_hash(self):
        for field_type in dir(FieldDescriptor):
            if field_type.startswith(PROTO_TYPE_PREFIX):
                self.type_hash[getattr(FieldDescriptor, field_type)] = field_type[len(PROTO_TYPE_PREFIX):].lower()


    def get_app(self):
        return self.app


    def get_type_hash(self):
        return self.type_hash


    def get_objects(self):
        return self.generated_objects


    ''' Generates a function that will return the listing for the specific object name '''
    def generate_list_routing(self, object_):
        def _function():
            fields = get_proto_fields(object_)
            object_name = get_name(object_).lower()
            entries = self.db.get_list_sql(object_)
            return render_template(object_name + "_list" + HTML_FILE_SUFFIX, title=object_name, entries=entries)
        return _function


    ''' Generates a function that will return the rendering for the specific object name '''
    def generate_view_routing(self, object_):
        def _function(**kwargs):
            fields = get_proto_fields(object_)
            object_name = get_name(object_).lower()
            sql = self.db.get_view_sql(object_)
            cur = self.db.execute(sql)
            args = {}
            args["entry"] = cur.fetchall()[0]
            args["title"] = get_name(object_)
            return render_template(get_name(object_).lower() + "_view" + HTML_FILE_SUFFIX, **args)
        return _function


    ''' Generates a function that will return the rendering for the new-object form for the specific object name. '''
    def generate_new_routing(self, object_):
        def _function():
            return render_template(get_name(object_).lower() + "_new" + HTML_FILE_SUFFIX, title="New" + get_name(object_))
        return _function


    ''' Generates a function that will add a specified object to the database. '''
    def generate_add_routing(self, object_):
        def _function():
            fields = get_proto_fields(object_)
            sql = self.db.get_add_sql(object_)
            self.db.execute(sql, map(lambda field: request.form[field.name], fields))
            self.db.commit()

            return redirect('/%s/%s/' % (get_name(object_).lower(), request.form['id']))
        return _function


    ''' Builds the URL routings from the objects we have. '''
    def build_routing(self, object_):
        lower_name = get_name(object_).lower()
        self.app.add_url_rule('/%s/' % lower_name, "%s_list" % lower_name, self.generate_list_routing(object_)) # List
        self.app.add_url_rule('/%s/<id>/' % lower_name, "%s_view" % lower_name, self.generate_view_routing(object_)) # View
        self.app.add_url_rule('/%s/new/' % lower_name, "%s_new" % lower_name, self.generate_new_routing(object_)) # New
        self.app.add_url_rule('/%s/add/' % lower_name, "%s_add" % lower_name, self.generate_add_routing(object_), methods=["POST"]) # Add


    def register_db_connections(self):
        def before_request():
            self.db = self.connect_db()
        def after_request(response):
            self.db.close()
            return response
        self.app.before_request(before_request)
        self.app.after_request(after_request)