import os, subprocess, sys
import urllib
from google.protobuf.message import Message
from google.protobuf.descriptor import FieldDescriptor
from flask import Flask, render_template, request, redirect
from utilities import source_dir, destination_dir, html_dir, static_dir, HTML_FILE_SUFFIX, PROTO_FILE_SUFFIX, PYTHON_FILE_SUFFIX, PYTHON_GENERATED_SUFFIX, PROTO_TYPE_PREFIX
from html import HTMLGenerator
from storage import DBStorage
from meta_objects import MetaObjects
from zipfile import ZipFile

class Cruddy:
    
    def __init__(self):
        self.type_hash = {}
        self.generated_names = []

        self.app = Flask(__name__)

        # At this point it's just a few method calls.
        self.verify_structure()
        self.meta_objects = MetaObjects(self)
        self.storage = DBStorage(self)
        self.html = HTMLGenerator(self)
        self.register_db_connections()

        # Create the HTML routings.
        for generated_object in self.meta_objects.objects:
            self.build_routing(generated_object)

        # Download Twitter Bootstrap and extract it. This could be done better.
        files = os.listdir(".")
        if "static" not in files:
            if "bootstrap.zip" not in files:
                print "Downloading Twitter Bootstrap..."
                urllib.urlretrieve("http://twitter.github.com/bootstrap/assets/bootstrap.zip", "bootstrap.zip")

            with ZipFile('bootstrap.zip', 'r') as myzip:
                myzip.extractall()

            os.rename("bootstrap", "static")
            print "Done!"


    def verify_structure(self):
        ''' Verifies the structure of the current working directory to make sure we have everything we need. '''
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


    def ensure_dir(self, dirname, files):
        ''' Ensures that a given directory exists in the current working directory. '''
        if dirname not in files:
            os.mkdir(dirname)


    def get_app(self):
        return self.app


    def get_type_hash(self):
        return self.meta_objects.type_hash


    def get_objects(self):
        return self.meta_objects.objects


    def generate_list_routing(self, meta_object):
        ''' Generates a function that will return the listing for the specific object name '''
        def _function():
            name = meta_object.name.lower()
            entries = self.storage.get_entries(meta_object)
            return render_template(name + "_list" + HTML_FILE_SUFFIX, title=name, entries=entries)
        return _function


    def generate_view_routing(self, meta_object):
        ''' Generates a function that will return the rendering for the specific object name '''
        def _function(**kwargs):
            entry = self.storage.get_entry(meta_object, kwargs["id"])
            title = meta_object.name
            return render_template(meta_object.name.lower() + "_view" + HTML_FILE_SUFFIX, title=title, entry=entry)
        return _function


    def generate_new_routing(self, meta_object):
        ''' Generates a function that will return the rendering for the new-object form for the specific object name. '''
        def _function():
            return render_template(meta_object.name.lower() + "_new" + HTML_FILE_SUFFIX, title="New" + meta_object.name)
        return _function


    def generate_add_routing(self, meta_object):
        ''' Generates a function that will add a specified object to the database. '''
        def _function():
            fields = meta_object.fields
            self.storage.add_entry(meta_object, request.form, request.form['id'])
            return redirect('/%s/%s/' % (meta_object.name.lower(), request.form['id']))
        return _function


    def build_routing(self, meta_object):
        ''' Builds the URL routings from the objects we have. '''
        lower_name = meta_object.name.lower()
        self.app.add_url_rule('/%s/' % lower_name, "%s_list" % lower_name, self.generate_list_routing(meta_object)) # List
        self.app.add_url_rule('/%s/<id>/' % lower_name, "%s_view" % lower_name, self.generate_view_routing(meta_object)) # View
        self.app.add_url_rule('/%s/new/' % lower_name, "%s_new" % lower_name, self.generate_new_routing(meta_object)) # New
        self.app.add_url_rule('/%s/add/' % lower_name, "%s_add" % lower_name, self.generate_add_routing(meta_object), methods=["POST"]) # Add


    def register_db_connections(self):
        def before_request():
            self.storage.open()
        def after_request(response):
            self.storage.close()
            return response
        self.app.before_request(before_request)
        self.app.after_request(after_request)