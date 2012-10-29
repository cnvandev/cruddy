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
        self.db = DBStorage(self)
        self.html = HTMLGenerator(self)

        # Create the HTML routings.
        for generated_object in self.meta_objects.objects:
            self.build_routing(generated_object)

        # Download Twitter Bootstrap and extract it. This could be done better.
        files = os.listdir(".")
        if "static" not in files:
            if "bootstrap.zip" not in files:
                print "Downloading Twitter Bootstrap..."
                urllib.urlretrieve ("http://twitter.github.com/bootstrap/assets/bootstrap.zip", "bootstrap.zip")

            with ZipFile('bootstrap.zip', 'r') as myzip:
                myzip.extractall()

            os.rename("bootstrap", "static")
            print "Done!"


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


    def get_app(self):
        return self.app


    def get_type_hash(self):
        return self.meta_objects.type_hash


    def get_objects(self):
        return self.meta_objects.objects


    ''' Generates a function that will return the listing for the specific object name '''
    def generate_list_routing(self, meta_object):
        def _function():
            fields = meta_object.fields
            name = meta_object.name.lower()
            entries = self.db.get_list_sql(meta_object)
            return render_template(name + "_list" + HTML_FILE_SUFFIX, title=name, entries=entries)
        return _function


    ''' Generates a function that will return the rendering for the specific object name '''
    def generate_view_routing(self, meta_object):
        def _function(**kwargs):
            fields = meta_object.fields
            name = meta_object.name.lower()
            sql = self.db.get_view_sql(meta_object)
            cur = self.db.execute(sql)
            args = {}
            args["entry"] = cur.fetchall()[0]
            args["title"] = meta_object.name
            return render_template(meta_object.name.lower() + "_view" + HTML_FILE_SUFFIX, **args)
        return _function


    ''' Generates a function that will return the rendering for the new-object form for the specific object name. '''
    def generate_new_routing(self, meta_object):
        def _function():
            return render_template(meta_object.name.lower() + "_new" + HTML_FILE_SUFFIX, title="New" + meta_object.name)
        return _function


    ''' Generates a function that will add a specified object to the database. '''
    def generate_add_routing(self, meta_object):
        def _function():
            fields = meta_object.fields
            sql = self.db.get_add_sql(meta_object)
            self.db.execute(sql, map(lambda field: request.form[field.name], fields))
            self.db.commit()

            return redirect('/%s/%s/' % (meta_object.name.lower(), request.form['id']))
        return _function


    ''' Builds the URL routings from the objects we have. '''
    def build_routing(self, meta_object):
        lower_name = meta_object.name.lower()
        self.app.add_url_rule('/%s/' % lower_name, "%s_list" % lower_name, self.generate_list_routing(meta_object)) # List
        self.app.add_url_rule('/%s/<id>/' % lower_name, "%s_view" % lower_name, self.generate_view_routing(meta_object)) # View
        self.app.add_url_rule('/%s/new/' % lower_name, "%s_new" % lower_name, self.generate_new_routing(meta_object)) # New
        self.app.add_url_rule('/%s/add/' % lower_name, "%s_add" % lower_name, self.generate_add_routing(meta_object), methods=["POST"]) # Add


    def register_db_connections(self):
        def before_request():
            self.db = self.connect_db()
        def after_request(response):
            self.db.close()
            return response
        self.app.before_request(before_request)
        self.app.after_request(after_request)