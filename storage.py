from __future__ import with_statement
import sqlite3
from contextlib import closing

class DBStorage:
    DEBUG = True

    SECRET_KEY = 'some key'
    USERNAME = 'admin'
    PASSWORD = 'default'

    schema_file = "schema.sql"
    database = 'storage.db'

    def __init__(self, cruddy):
        self.cruddy = cruddy
        self.generate_all_schema(cruddy.get_objects())
        self.setup_db(self.schema_file)


    ''' Opens the storage for use. YOU are required to close it! Don't forget! '''
    def open(self):
        self.db_connection = sqlite3.connect(self.database)


    ''' Closes the opened storage system after use. '''
    def close(self):
        self.connection.close()


    ''' Returns a database connection object. '''
    def setup_db(self, schema_file):
        self.open()
        f = open(schema_file)
        self.db_connection.cursor().executescript(f.read())
        self.db_connection.commit()
        self.close()


    ''' Gets a list of entries from storage. '''    
    def get_entries(self, meta_object):
        sql = self.get_list_sql(meta_object)
        return self.db_connection.execute(sql)


    ''' Gets a single entry from storage. '''    
    def get_entry(self, meta_object, id):
        sql = self.get_view_sql(meta_object)
        cur = self.db_connection.execute(sql, id)
        return cur.fetchall()[0]


    ''' Puts a single entry into storage. '''
    def add_entry(self, meta_object, id):
        sql = self.get_add_sql(meta_object)
        self.db_connection.execute(sql)


    ''' Builds and outputs a schema file for the list of objects given. '''
    def generate_all_schema(self, meta_objects):
        output_file = open(self.schema_file, 'w')
        for meta_object in self.cruddy.meta_objects.objects:
            output_file.write(self.generate_schema(meta_object))
        output_file.close


    ''' Builds a SQL statement that defines a schema for a table that can hold the given object. '''
    def generate_schema(self, meta_object):
        name = meta_object.name.lower()

        schema_sql = "drop table if exists %s;\ncreate table %s (\n" % (name, name)
        column_descriptors = []
        for field in meta_object.fields:
            column_name = field["name"]
            column_type = field["type"].replace("int32", "integer")
            if field["name"] is "id":
                column_type += " primary key autoincrement"
            column_descriptors.append("  %s %s" % (column_name, column_type))
        schema_sql += ",\n".join(column_descriptors)
        schema_sql += ");"

        return schema_sql


    def get_list_sql(self, meta_object):
        name = meta_object.name.lower()
        fields = meta_object.fields

        return 'select %s from %s order by id desc' % (", ".join(map(lambda field: field["name"].lower(), fields)), name)


    def get_add_sql(self, meta_object):
        name = meta_object.name.lower()
        fields = meta_object.fields

        return "insert into %s (%s) values (%s)" % (name, ", ".join(map(lambda field: field["name"].lower(), fields)), ", ".join(map(lambda field: "?", fields)))


    def get_view_sql(self, meta_object):
        name = meta_object.name.lower()
        fields = meta_object.fields

        return 'select %s from %s where id = %s' % (", ".join(map(lambda field: field["name"].lower(), fields)), name, fields['id'])