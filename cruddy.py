from html import HTMLGenerator
from storage import DBStorage
from meta_objects import MetaObjects
from flaskrer import Flaskrer
from housekeeper import Housekeeper

class Cruddy:
    
    def __init__(self):
        # At this point it's all object delegation.
        self.meta_objects = MetaObjects(self)
        self.storage = DBStorage(self)
        self.html = HTMLGenerator(self)
        self.flaskrer = Flaskrer(self)
        self.housekeeper = Housekeeper(self)


    def start(self):
        ''' Actually starts the app. '''
        self.flaskrer.run()
        
    def get_objects(self):
        return self.meta_objects.objects