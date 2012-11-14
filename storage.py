from __future__ import with_statement
import sqlite3
import os
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
        self.db_connection = None

        # If it exists, don't clobber it away!
        destroy = "Y"
        if os.path.exists(self.database):
            destroy = raw_input("Database exists! Should I destroy? [Y]: ")

        if destroy.lower() is "y":
            self.generate_all_schema(cruddy.get_objects())
            self.setup_db(self.schema_file)


    def open(self):
        ''' Opens the storage for use. YOU are required to close it! Don't forget! '''
        self.db_connection = sqlite3.connect(self.database)


    def close(self):
        ''' Closes the opened storage system after use. '''
        self.db_connection.close()
        self.db_connection = None


    def setup_db(self, schema_file):
        ''' Returns a database connection object. '''
        self.open()
        self.load_schema(schema_file)
        self.close()


    def load_schema(self, schema_file):
        f = open(schema_file)
        self.db_connection.cursor().executescript(f.read())
        self.db_connection.commit()


    def get_entries(self, meta_object):
        ''' Gets a list of entries from storage. '''    
        sql = self.get_list_sql(meta_object)
        cur = self.db_connection.execute(sql)
        entries = [self.dict_factory(cur, result) for result in cur.fetchall()]
        return entries


    def get_entry(self, meta_object, id):
        ''' Gets a single entry from storage. '''
        sql = self.get_view_sql(meta_object)
        cur = self.db_connection.execute(sql, id)
        return self.dict_factory(cur, cur.fetchone())


    def dict_factory(self, cursor, row):
        ''' Returns a dict of cursor results with the column names as keys. '''
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d


    def add_entry(self, meta_object, data, id):
        ''' Puts a single entry into storage. '''
        sql = self.get_add_sql(meta_object)
        data_for_object = map(lambda field: data[field["name"]], meta_object.fields)
        self.db_connection.execute(sql, data_for_object)
        self.db_connection.commit()


    def generate_all_schema(self, meta_objects):
        ''' Builds and outputs a schema file for the list of objects given. '''
        output_file = open(self.schema_file, 'w')
        for meta_object in self.cruddy.meta_objects.objects:
            output_file.write(self.generate_schema(meta_object))
        output_file.close


    def generate_schema(self, meta_object):
        ''' Builds a SQL statement that defines a schema for a table that can hold the given object. '''
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

        return 'select %s from %s where id = ?' % (", ".join(map(lambda field: field["name"].lower(), fields)), name)