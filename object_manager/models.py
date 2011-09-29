from model_helpers import fetch_uri, classify_uri, get_object_uri,is_object,delete_obj, parse_objects_into_buckets, RDFObjectHelper, declassify_uri
from exceptions import RDFNoUriException, RDFObjectNoUriException, RDFDeletionException, RDFObjectPersistanceException
from ..triple_manager.lib import save_triples,find_triples

"""
The collection of classes and helper methods that
serve as the object interface to the RDF Mapper system.
All objects intended to be represented as RDF triples
extend classes in this module.
"""
# Helpers

def define_predicate():
    """
    helper for models to create class level pred. attributes
    """
    return RDFPredicate()

def define_uri(auto=False):
    """
    helper method that created a URI predicate
    """
    return RDFPredicate(is_uri=True, auto_uri=auto)
     
# Models
        
class RDFPredicate(object):
    """
    Represents an RDF Predicate.
    It is used to create attributes on RDFSubject classes.
    """
    
    def __init__(self, is_uri=False, auto_uri=False):
        self.is_uri = is_uri
        self.auto_uri = auto_uri

class RDFSubjectMeta(type):
    """
    Meta class included on all subclasses of RDFSubject class.
    Introduces key class level attributes, but also serves as an
    expandable piece of architecture for further use.
    """
    
    def __new__(meta, classname, supers, classdict):
        pred_names = [key for key in classdict if isinstance(classdict[key],RDFPredicate)]
        classdict['predicates'] = pred_names
        return type.__new__(meta, classname, supers, classdict)

class RDFSubject(object):
    """
    The class all classes wishing to participate in the
    RDF Mapper system must extend to be a part of the application's
    RDF graph. Extension of this class is the mechanism that enables all
    RDF Mapper functionality for a class(CRUD,searching,etc).
    """

    __metaclass__ = RDFSubjectMeta 
    
    @classmethod
    def find(cls,**kwargs):
        """
        Class level method that allows criteria based searching
        of all instances of the given class.
        cls - the class type the determines the type limits of the search
        kwargs - hash of search criteria(where clause),cardinality(first,all,etc), and potentially many more
        """
        session = cls._session
        objects = []
        object_buckets = {}
        where_clause = kwargs.get('where')
        cls_name = cls.__name__.lower()
        # tells the triple manager layer to do all the searching
        if where_clause:
            object_triples_tuple = find_triples(cls_name,session,where_clause)
        else:    
            object_triples_tuple = find_triples(cls_name,session)
        # get all the object attributes in buckets(hashes that represent an object's attributes)
        object_buckets = parse_objects_into_buckets(object_triples_tuple[0],object_triples_tuple[1])
        for uri,attribute_dict in object_buckets.iteritems():
            obj_inst = cls()
            # goes through each bucket
            for attr_name,attr_val in attribute_dict.iteritems():
                # sets attributes on the newly created object
                setattr(obj_inst,attr_name,attr_val)
            # assign back the auto_uri value
            auto_uri_field_name =  obj_inst.auto_uri_field_name()
            # if the object class def says the URI is auto genned
            if auto_uri_field_name:
                raw_uri = declassify_uri(uri)
                # set the URI field
                setattr(obj_inst,auto_uri_field_name,raw_uri)
            objects.append(obj_inst)
        if kwargs.get('match') == 'first':
            if len(objects) > 0:
                objects = objects[0] 
            else:
                objects = None
        # mark all objects as persisted given they were just
        # retrieved from the db
        def set_persisted(obj):
            obj._persisted = True
            return obj
        # set the persisted flag on all returned objects
        if isinstance(objects,list):
            objects = map(set_persisted,objects)
        else:
            # if only one object returned, set its persisted flag as well
            if objects != None:    
                set_persisted(objects)
        return objects
    
    @classmethod
    def uri_pred(cls):
        """
        returns the attribute of the class 
        that represents the class's uri value
        cls - the class
        """
        pred = None
        predicates = cls.predicates
        for pred_name in predicates:
            class_pred_val = cls.__dict__[pred_name]
            if class_pred_val.is_uri:
                pred = pred_name
        return pred
    
    @classmethod
    def find_by_uri(cls,uri,full=False):
        """
        An abstraction of the find method that allows
        for quick searching using a URI value
        cls - The class type we are searching for
        uri - the URI we are looking for
        full - boolean that represents the state of the URI...
        is it class relative or fully expressed in the form {class_name}/uri_val
        """
        if full == False:
            uri = classify_uri(cls,uri)
        obj = None
        uri_pred = cls.uri_pred()
        if uri_pred:
            if cls.__dict__[uri_pred].auto_uri:
                obj = cls.find(where={ 'auto_uri' : uri}, match='first')
            else:
                obj = cls.find(where={ uri_pred : uri}, match='first')
        else:
            raise RDFNoUriException(None,1)
        return obj

    def __new__(typ,**kwargs):
        """
        Sets initial predicate values and other
        system dependent state variables
        """
        obj = object.__new__(typ)
        # setup predicate vals
        for pred_name in obj.__class__.predicates:
            # only sets defined pred attributes
            pred_val = kwargs.get(pred_name)
            setattr(obj,pred_name,pred_val)
        # cannot be persisted yet
        setattr(obj,"_persisted",False)
        return obj
    
    def __getattribute__(self, attr):
        """
        Attribute access intercept designed to 
        enable lazy loading. If the attribute being accessed is
        an RDFObjectHelper, this method does the retrieval
        """
        attr_val = object.__getattribute__(self, attr)
        # if it is a list, check each entry in the list
        if isinstance(attr_val, list):
            attr_list_vals = []
            for single_attr_val in attr_val:
                if isinstance(single_attr_val,RDFObjectHelper):
                    obj_class_type = single_attr_val.get_object_type(RDFSubject)
                    if obj_class_type:
                        # load of the RDFSubject class in the list
                        obj = obj_class_type.find_by_uri(single_attr_val.full_uri,True)
                        if obj:
                            attr_list_vals.append(obj)
                    else:
                        raise RDFObjectPersistanceException(2)
            attr_val = attr_list_vals
        else:
            # if it is not a list
            if isinstance(attr_val,RDFObjectHelper):
                obj_class_type = attr_val.get_object_type(RDFSubject)
                if obj_class_type:
                    # load the RDFSubject class
                    obj = obj_class_type.find_by_uri(attr_val.full_uri,True)
                    # and assign as the attribute value
                    attr_val = obj
                else:
                    raise RDFObjectPersistanceException(2)
        return attr_val

    def __str__(self):
        """
        Default String representation of all RDFSubject subclasses
        """
        vals = ["{0}: {1}".format(pred_name,self.__dict__[pred_name]) for pred_name in self.__class__.predicates]
        return "\n".join(vals)
        
    def get_uri(self):
        """
        Retrieves the URI from this RDFSubject class instance
        """
        uri = None
        predicates = self.__class__.predicates
        for pred_name in predicates:
            class_pred_val = self.__class__.__dict__[pred_name]
            if class_pred_val.is_uri:
                uri = self.__dict__[pred_name] 
        return uri
    
    def is_persisted(self):
        """
        Helper to check persistance state of an RDFSubject instance
        """
        return self._persisted
    
    def auto_uri_field_name(self):
        """
        Determines the attribute name that holds
        the auto generate URI value(if there is one)
        """
        field_name = None
        predicates = self.__class__.predicates
        for pred_name in predicates:
            class_pred_val = self.__class__.__dict__[pred_name]
            if class_pred_val.is_uri:
                if class_pred_val.auto_uri:
                    field_name = pred_name
        return field_name
        
    def delete(self):
        """
        Deletes an RDFSubject instance from the db
        """
        session = self.__class__._session
        deleted = False
        uri = self.get_uri()
        if uri:
            complete_uri = classify_uri(self.__class__, uri)
            # check if it is an object to another subject
            if is_object(complete_uri, session):
                # if so, cannot delete if there are active 
                # references to this object
                raise RDFDeletionException(2)
            else:
                deleted = delete_obj(complete_uri, session)
        else:
            # no URI, no delete
            raise RDFDeletionException(1)
        self._persisted = False
        return deleted
        
    
    def save(self):
        """
        Saves this RDFSubject class to the db
        """
        session = self.__class__._session
        saved = False
        raw_uri = fetch_uri(self,session)
        if raw_uri:
            # clean up the URI for saving in shared datastore
            uri = classify_uri(self.__class__,raw_uri)
            auto_uri_field_name = self.auto_uri_field_name()
            if auto_uri_field_name != None:
                # assigns auto uri val at save time
                self.__dict__[auto_uri_field_name] = raw_uri
            triples = []
            triples_with_datatype = []
            pred_names = self.__class__.predicates
            for pred_name in pred_names:
                if auto_uri_field_name == pred_name:
                    continue
                pred_val = self.__dict__[pred_name]
                # dont save None value predicates as triples
                if pred_val == None:
                    continue
                # if the attribute is a list or tuple
                # we save each entry as a seprate triple
                if isinstance(pred_val, list) or isinstance(pred_val, tuple):
                    for val in pred_val:
                        if isinstance(val,RDFSubject):
                            object_uri = get_object_uri(val,session)
                            if object_uri:
                                if val.is_persisted():
                                    # create triple
                                    triples.append((uri,pred_name,object_uri))
                                else:
                                    # the object of this Subject has not yet been persisted
                                    raise RDFObjectPersistanceException(1)
                            else:
                                # raise No URI error for object
                                raise RDFObjectNoUriException(val)
                        else:
                            # the predicate val is not a Subject, just a plain Python type
                            # create quadruple
                            triples_with_datatype.append((uri,pred_name,val.__class__.__name__,val))
                else:
                    # not a list, single val
                    if isinstance(pred_val,RDFSubject):
                        object_uri = get_object_uri(pred_val,session)
                        if object_uri:
                            if pred_val.is_persisted():
                                # create triple
                                triples.append((uri,pred_name,object_uri))
                            else:
                                raise RDFObjectPersistanceException(1)
                        else:
                            # raise NO URI from object
                            raise RDFObjectNoUriException(pred_val)
                    else:
                        # the predicate val is not a Subject, just a plain Python type
                        #create quadruple eval of of string
                        triples_with_datatype.append((uri,pred_name,pred_val.__class__.__name__,pred_val))
        else:
            raise RDFNoUriException(self)
        # calls triple manager here...passes triples for saving
        saved = save_triples(triples,triples_with_datatype, session)
        if saved:
            self._persisted = True
        return saved
        