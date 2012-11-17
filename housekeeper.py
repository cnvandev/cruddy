import os
import urllib
from zipfile import ZipFile
from utilities import source_dir, destination_dir, html_dir, static_dir, PROTO_FILE_SUFFIX, BOOTSTRAP_URL, ZIP_FILE_SUFFIX

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
        bootstrap_file = BOOTSTRAP_URL.split("/")[-1]

        files = os.listdir(".")
        if static_dir not in files:
            if bootstrap_file not in files:
                print "Downloading Twitter Bootstrap..."
                urllib.urlretrieve(BOOTSTRAP_URL, bootstrap_file)

            with ZipFile(bootstrap_file, 'r') as myzip:
                myzip.extractall()

            # The folder name that the zipfile extracts to is the same as the zipfile name, sans suffix.
            bootstrap_folder = bootstrap_file[0:-len(ZIP_FILE_SUFFIX)]
            os.rename(bootstrap_folder, static_dir)
            print "Done!"