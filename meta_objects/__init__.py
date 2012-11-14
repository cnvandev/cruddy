import subprocess
import sys
import os
from google.protobuf.message import Message
from google.protobuf.descriptor import FieldDescriptor
from utilities import source_dir, destination_dir, html_dir, static_dir, HTML_FILE_SUFFIX, PROTO_FILE_SUFFIX, PYTHON_FILE_SUFFIX, PYTHON_GENERATED_SUFFIX, PROTO_TYPE_PREFIX
from metaobject import MetaObject

class MetaObjects:

    def __init__(self, cruddy):
        self.cruddy = cruddy

        self.type_hash = self.build_type_hash()
        self.verify_structure()
        self.objects = self.generate_protos()


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


    def generate_protos(self):
        ''' Generates our MetaObjects (and the underlying Python objects) from the proto files. '''
        generated = []
        for proto in os.listdir(source_dir):
            generated.append(MetaObject(self, proto))
        return generated


    ''' Creates a hash of the ProtocolBuffer types we have available, for lookup. '''
    def build_type_hash(self):
        type_hash = {}
        for field_type in dir(FieldDescriptor):
            if field_type.startswith(PROTO_TYPE_PREFIX):
                type_hash[getattr(FieldDescriptor, field_type)] = field_type[len(PROTO_TYPE_PREFIX):].lower()
        return type_hash