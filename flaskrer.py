from flask import Flask, render_template, request, redirect
from utilities import HTML_FILE_SUFFIX

class Flaskrer:

    def __init__(self, cruddy):
        ''' Initializes the Flask controller, registers the routings and database connections. '''
        self.cruddy = cruddy
        self.app = Flask(__name__)
        
        # Create the HTML routings.
        for generated_object in self.cruddy.get_objects():
            self.build_routing(generated_object)

        self.register_db_connections()
        

    def run(self):
        ''' Starts up the app! '''
        self.app.run(debug=True)


    def generate_list_routing(self, meta_object):
        ''' Generates a function that will return the listing for the specific object name '''
        def _function():
            name = meta_object.name.lower()
            entries = self.cruddy.storage.get_entries(meta_object)
            return render_template(name + "_list" + HTML_FILE_SUFFIX, title=name, entries=entries)
        return _function


    def generate_view_routing(self, meta_object):
        ''' Generates a function that will return the rendering for the specific object name '''
        def _function(**kwargs):
            entry = self.cruddy.storage.get_entry(meta_object, kwargs["id"])
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
            self.cruddy.storage.add_entry(meta_object, request.form, request.form['id'])
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
        ''' Registers the database opening with the start of a request, and closing with the end of a request. '''
        def before_request():
            self.cruddy.storage.open()
        def after_request(response):
            self.cruddy.storage.close()
            return response
        self.app.before_request(before_request)
        self.app.after_request(after_request)