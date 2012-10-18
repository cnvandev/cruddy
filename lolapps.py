import subprocess
import sys
import os
from google.protobuf.message import Message
from google.protobuf.descriptor import FieldDescriptor
from flask import Flask, render_template

PROTO_FILE_SUFFIX = ".proto"
PYTHON_FILE_SUFFIX = ".py"
HTML_FILE_SUFFIX = ".html"

PYTHON_GENERATED_SUFFIX = "_pb2"
PROTO_TYPE_PREFIX = "TYPE_"

source_dir = "protos"
destination_dir = "objects"
html_dir = "templates"
static_dir = "static"

type_hash = {}
app = Flask(__name__)

''' Verifies the structure of the current working directory to make sure we have everything we need. '''
def verify_structure():
	# Make sure the source directory exists and has protos in it.
	files = os.listdir(".")
	if source_dir not in files:
		raise Exception("Couldn't find source directory %s" % source_dir)
	else:
		protos = os.listdir(source_dir)
		for proto in protos:
			if proto.endswith(".proto"):
				break
		else:
			raise Exception("Found no .proto files in source directory %s" % source_dir)

	# Make sure the destination and HTML dirs exist.
	ensure_dir(destination_dir, files)
	ensure_dir(html_dir, files)


''' Ensures that a given directory exists in the current working directory. '''
def ensure_dir(dirname, files):
	if dirname not in files:
		os.mkdir(dirname)


''' Generates the Protocol Buffer objects from the .proto files in the source directory. Assumes everything is there and in working order. '''
def generate_protos():
	generated = []
	for proto in os.listdir(source_dir):
		try:
			subprocess.check_output(["protoc", "-I=%s" % source_dir, "--python_out=%s" % destination_dir, "%s/%s" % (source_dir, proto)]);
			object_name = proto[:len(PROTO_FILE_SUFFIX)]
			generated.append(object_name + PYTHON_GENERATED_SUFFIX)
		except Exception as ex:
			sys.exit()


	return generated


''' Imports the given list as a series of objects to be brought into the current workspace. '''
def import_proto(proto_objects):
	sys.path.append(destination_dir)
	modules = map(__import__, proto_objects)
	objects = []
	for name in proto_objects:
		objects.append(getattr(sys.modules[name], name[:-len(PYTHON_GENERATED_SUFFIX)])())
	return objects


''' Clears the HTML page directory '''
def clear_html_pages():
	html_files = os.listdir(html_dir)
	for html_file in html_files:
		path = os.path.join(html_dir, html_file)
		if os.path.isfile(path):
			os.unlink(path)


''' Generates an HTML page for the object! '''
def generate_html_page(object_):
	if not isinstance(object_, Message):
		raise Exception("You should only be generating HTML of Protocol Buffer objects!")

	name = object_.__class__.__name__
	output_file = open(os.path.join(html_dir, name + HTML_FILE_SUFFIX), 'w')
	output_file.write('''
	<html>
		<head>
			<title>%s</title>
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
		          </div><!--/.nav-collapse -->
		        </div>
		      </div>
		    </div>

			<div class="container">
	''' % name)

	output_file.write("<h1>%s</h1>" % name)

	for field in object_.DESCRIPTOR.fields:
		output_file.write('''<p><span class="muted">%s</span> %s</p>''' % (type_hash[field.type], field.name))
	output_file.write('''
			</div>
			<script src="http://code.jquery.com/jquery-latest.js"></script>
			<script src="/static/js/bootstrap.min.js"></script>
		</body>
	</html>
	''')
	output_file.close()


''' Creates a hash of the ProtocolBuffer types we have available, for lookup. '''
def build_type_hash():
	for field_type in dir(FieldDescriptor):
		if field_type.startswith(PROTO_TYPE_PREFIX):
			type_hash[getattr(FieldDescriptor, field_type)] = field_type[len(PROTO_TYPE_PREFIX):].lower()


@app.route('/person/')
def hello():
    return render_template('Person.html')

if __name__ == "__main__":
	build_type_hash()

	# At this point it's just a few method calls.
	verify_structure()
	generated_names = generate_protos()
	generated = import_proto(generated_names)

	clear_html_pages()
	for generated_object in generated:
		generate_html_page(generated_object)

	app.run(debug=True)