import subprocess
import sys
from utilities import source_dir, destination_dir, html_dir, static_dir, HTML_FILE_SUFFIX, PROTO_FILE_SUFFIX, PYTHON_FILE_SUFFIX, PYTHON_GENERATED_SUFFIX, PROTO_TYPE_PREFIX

class MetaObject:

    def __init__(self, meta_objects, proto):
        self.proto_file = proto
        self.meta_objects = meta_objects
        self.name = proto[:len(PROTO_FILE_SUFFIX)]
        self.python_file = self.name + PYTHON_GENERATED_SUFFIX + PYTHON_FILE_SUFFIX
        self.module = self.name + PYTHON_GENERATED_SUFFIX

        self.generate_from_proto(self.proto_file)
        self.import_object(self.python_file)

        self.object = getattr(sys.modules[self.python_file[:-len(PYTHON_FILE_SUFFIX)]], self.name)()

        # The fields...field...is a list of dicts containing the field and its type.
        self.fields = map(lambda field: {"name": field.name, "type": self.meta_objects.type_hash[field.type]}, self.get_proto_fields(self.object))


    @staticmethod
    def get_proto_fields(object_):
        ''' Returns a list of the fields on an object generated by Protocol Buffers. '''
        return object_.DESCRIPTOR.fields


    @staticmethod
    def generate_from_proto(proto):
        ''' Runs the Protocol Buffer generation command '''
        subprocess.check_output(["protoc", "-I=%s" % source_dir, "--python_out=%s" % destination_dir, "%s/%s" % (source_dir, proto)]);


    @staticmethod
    def import_object(python_file):
        ''' Imports the given object into the current workspace. '''
        if destination_dir not in sys.path:
            sys.path.append(destination_dir)
        __import__(python_file[:-len(PYTHON_FILE_SUFFIX)])