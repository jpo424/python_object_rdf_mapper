from ..sql_manager.lib import get_id
from ..sql_manager.models import Triple,TripleObjectInferred
from exceptions import RDFNoUriException

"""
Collection of helper methods used in
Models module, most often by the RDFSubject class.
These do a lot of heavey lifting and primarily serve
to better encapsulate functionality that, in theory,
could be used somewhere else.(or just to hide really complex stuff
a model instance should not know how to do) 
"""

def get_class_type(class_name,rdfsubject_class):
    """
    retrieves the proper rdf subject sub class
    
    class_name - the string val of the desired class type
    used to match against rdf subject sub classes
    rdfsubject_class - the RDFSubject class constant
    """
    classes = []
    class_type = None
    # inline definition of a recursive function
    # that searches through all subclasses of the given subject class
    def search_for_classes(subject_class,seen_classes):
        subclasses = subject_class.__subclasses__()
        seen_classes.append(subject_class)   
        for subclass in subclasses:
            if subclass not in seen_classes:
                seen_classes = search_for_classes(subclass,seen_classes) 
        return seen_classes
    classes = search_for_classes(rdfsubject_class,[])
    # after getting all RDFSubject subclasses, see if there is a match
    for cl in classes:
        if class_name == cl.__name__:
            # match found, return class constant
            class_type = cl
    return class_type
    
    
class RDFObjectHelper(object):
    """
    to enable lazy loading, this class serves as a stand-in
    for attributes of an RDFSUbject sub class that are subject
    classes themselves
    """
    def __init__(self,full_uri):
        self.full_uri = full_uri
        self.class_name = str(full_uri[0:full_uri.find('/')]).capitalize()
        
    def get_object_type(self,rdfsubject_class):
        return get_class_type(self.class_name,rdfsubject_class)
        
def fetch_uri(obj,session):
    """
    Returns the URI val of an RDFSubject object
    (both auto URIs and instance assigned URIs)
    obj - the RDFSubject subclass instance
    session - the SQLAlchemy db session
    """
    uri = None
    predicates = obj.__class__.predicates
    for pred_name in predicates:
        class_pred_val = obj.__class__.__dict__[pred_name]
        # if we find the uri attribute
        if class_pred_val.is_uri:
            if class_pred_val.auto_uri:
                # retrieve the uri via id fetch in db
                uri = get_id(session)
            else:
                # get the uri val
                uri = obj.__dict__[pred_name]
                if isinstance(uri, list) or isinstance(uri, tuple):
                    raise RDFNoUriException(obj,3)
    return uri
    
def classify_uri(obj_class, uri):
    """
    formats the uri for storage in shared db table
    obj_class - the RDFSubjet class used to further uniquify 
    uri
    uri - the uri value
    """
    class_prefix = obj_class.__name__
    return "{0}/{1}".format(class_prefix.lower(), uri)
    
def declassify_uri(uri):
    """
    Decomposes the URI to its relative state for
    access via a RDFSubject's attribute accessor interface
    """
    slash_index = uri.find('/')
    raw_uri = uri[uri.find('/') + 1:len(uri)]
    return raw_uri

def get_object_uri(obj, session):
    """
    Gets the URI from an RDFSubject subclass instance
    obj - the RDFSubject object 
    session - the SQLAlchemy db session
    """
    uri = None
    raw_uri = obj.get_uri()
    if raw_uri:
        uri = classify_uri(obj.__class__,raw_uri)
    return uri   

def is_object(uri, session):
    """
    Determines if an RDFSubject instance
    is an object of another RDFSubject instance
    uri - the URI of the object we are checking
    session - the SQLAlchemy db session
    """
    referenced = False
    # check the db to see if the uri exists anywhere
    count = session.query(Triple).filter(Triple.object_uri == uri).count()
    session.commit()
    if count > 0:
        referenced = True
    return referenced
    
def delete_obj(uri,session):
    """
    Deletes an RDFSubject instnace from the db
    uri - The uri of the object to delete
    session - the SQLAlchemy db session
    """
    session.query(Triple).filter(Triple.subject_uri == uri).delete()
    session.query(TripleObjectInferred).filter(TripleObjectInferred.subject_uri == uri).delete()
    session.commit()
    return True
    
def parse_objects_into_buckets(triples,triples_with_datatype):
    """
    Given sets of triples, bucket the triples into groups of
    triples that belong to the same object. Each object is 
    represented as a hash of its attributes, values
    triples - list of sql model Triple classes
    triples_with_datatype - list of sql model TripleObjectInferred classes
    """
    # throw them together for easy parsing
    all_triples = set(triples) ^ set(triples_with_datatype) 
    object_buckets = {}
    for triple in all_triples:
        sub_uri = triple.subject_uri
        pred_uri = triple.predicate_uri
        if isinstance(triple,Triple):
            obj_uri = triple.object_uri
            obj_val = RDFObjectHelper(obj_uri)
        else:
            obj_type = eval(triple.object_type)
            obj_val = obj_type(triple.object_value)
        # parse each triple and pass it to a bucket
        object_buckets = parse_object_triple(object_buckets,sub_uri,pred_uri,obj_val)
    return object_buckets

def parse_object_triple(object_buckets,sub_uri,pred_uri,obj_val):
    """
    Given the values of a triple, place it in an appropriate object
    bucket or create a new bucekt for the values
    sub_uri - the subject of the uri this triple belongs to
    pred_uri - 
    obj_val - 
    """
    # if there is a bucket already for this triple
    if sub_uri in object_buckets.keys():
        # if the predicate of this triple already exists
        if pred_uri in object_buckets[sub_uri].keys():
            # get the current pred val
            bucket_obj_val = object_buckets[sub_uri][pred_uri]
            # if the pred val is a list, then this new triple val
            # gets added to the list
            if isinstance(bucket_obj_val, list):
                bucket_obj_val.append(obj_val)
                object_buckets[sub_uri][pred_uri] = bucket_obj_val
            else:
                # if it is not yet a list, but should be...make the list and add the val
                new_bucket_obj_val = [bucket_obj_val]
                new_bucket_obj_val.append(obj_val)
                object_buckets[sub_uri][pred_uri] = new_bucket_obj_val
        else:
            # new pred/ val, add it to object bucket
            object_buckets[sub_uri][pred_uri] = obj_val
    else:
        # creates a new bucket using this triple
        object_buckets[sub_uri] = {pred_uri : obj_val}
    return object_buckets
    
    
   
