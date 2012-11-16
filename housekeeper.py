import os, subprocess, sys
import urllib
from zipfile import ZipFile
from utilities import source_dir, destination_dir, html_dir, static_dir, HTML_FILE_SUFFIX, PROTO_FILE_SUFFIX, PYTHON_FILE_SUFFIX, PYTHON_GENERATED_SUFFIX, PROTO_TYPE_PREFIX

class Housekeeper:

    def __init__(self, cruddy):
        ''' Make sure the folder structure is what we need and we have the files we need. '''
        self.cruddy = cruddy

        self.verify_structure()
        self.ensure_twitter_bootstrap()


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
        ''' Ensures that a given directory exists in the given directory. '''
        if dirname not in files:
            os.mkdir(dirname)


    def ensure_twitter_bootstrap(self):
        ''' Downloads Twitter Bootstrap and extracts it so we can use it. This could be done better. '''
        files = os.listdir(".")
        if "static" not in files:
            if "bootstrap.zip" not in files:
                print "Downloading Twitter Bootstrap..."
                urllib.urlretrieve("http://twitter.github.com/bootstrap/assets/bootstrap.zip", "bootstrap.zip")

            with ZipFile('bootstrap.zip', 'r') as myzip:
                myzip.extractall()

            os.rename("bootstrap", "static")
            print "Done!"