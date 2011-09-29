from ..sql_manager.models import Triple, TripleObjectInferred

"""
Collection of functions that operate on in memory triples.
They serve as the interface between the RDF Model classes
and the SQLAlchemty Model classes. They disassemble RDF models
into triples consumable by SQLAlchemy models.
"""

def save_triples(triples,triples_with_datatype, session):
    """
    Takes triples that represent an RDFSubject's properties
    and saves them as SQLAlchemy model objects
    
    triples - array of triples(standard)
    triples_with_datatype - array of triples(where object is represented as
    two entries; its python datatype and its value)
    session - the SQLAlchemy db session
    """
    # save each triple as a sql Triple object
    for t in triples:
        # construct the triple instance
        triple = Triple()
        triple.subject_uri = t[0]
        triple.predicate_uri = t[1]
        triple.object_uri = t[2]
        # delete old version of triple if it exists...should do updates here in the future
        session.query(Triple).filter(Triple.subject_uri == triple.subject_uri).filter(Triple.predicate_uri == triple.predicate_uri).filter(Triple.object_uri == triple.object_uri).delete()
        session.add(triple)
    # save each triple as a TripleObjectInferred sql model object
    for t in triples_with_datatype:
        # build it
        triple = TripleObjectInferred()
        triple.subject_uri = t[0]
        triple.predicate_uri = t[1]
        triple.object_type = t[2]
        triple.object_value = str(t[3])
        # delete old version of triple
        session.query(TripleObjectInferred).filter(TripleObjectInferred.subject_uri == triple.subject_uri).filter(TripleObjectInferred.predicate_uri == triple.predicate_uri).filter(TripleObjectInferred.object_value == triple.object_value).delete()
        session.add(triple)
    session.commit() 
    # if not true returned, then we can assume some exception has been raised
    # an explicit True return simply allows this method to be used in conditional statements if required
    return True

def find_triples(cls_name,session,where_dict=None):
    """
    queries the db via the SQLAlchemy model classes 
    and returns a tuple of (array of triple objects, array of
    triple_object_inferred objects).

    cls_name - The string class name of the type of object we are searching for
    session - the SQLAlchemy session
    where_dict - dictionary of the object attribute : value used to specifiy the
    rows we are interested in.
    """
    find_subjects = False
    # format the class name a bit before using it to query
    # against subject_uri vals(of either model)
    cls_name_query_str = "{0}/%".format(cls_name)
    if where_dict:
        auto_uri_val = where_dict.get('auto_uri')
        # if we are looking for the triples of an object that has
        # an auto assigned URI, the query is easy...
        if auto_uri_val:
            # just find all the triples(of both models) that have the matching subject_uri...those are all
            # of the properties of the object
            triples = session.query(Triple).filter(Triple.subject_uri == auto_uri_val)
            triples_with_datatype = session.query(TripleObjectInferred).filter(TripleObjectInferred.subject_uri == auto_uri_val)
        else:   
            # else, not so simple
            # first, find the triples belonging to the same class type
            triples = session.query(Triple).filter(Triple.subject_uri.like(cls_name_query_str))
            triples_with_datatype = session.query(TripleObjectInferred).filter(TripleObjectInferred.subject_uri.like(cls_name_query_str))
            # now that we have the triples belonging to the proper class, use the attributes and values
            # in the where dict to find the exact set of triples we are interested in.
            # (equivalent to WHERE clause in SQL....so this is our WHERE operation across multiple triples)
            for attribute,value in where_dict.iteritems():
                # for each sqlalchemy model type, find the triples that have matching predicate and object vals 
                triples_with_datatype = triples_with_datatype.filter(TripleObjectInferred.predicate_uri == attribute)
                triples_with_datatype = triples_with_datatype.filter(TripleObjectInferred.object_value == str(value))
                triples = triples.filter(Triple.predicate_uri == attribute)
                triples = triples.filter(Triple.object_uri == str(value))
            # this means we now have a collection of properties that correctly match what we were looking for
            # ....now we need to find the rest of the properties attached to these objects(well we cant just return 
            # only part of an object!)
            find_subjects = True
    else:
        # if there was no where clause, then we want to find ALL of the triples of the given class name
        triples = session.query(Triple).filter(Triple.subject_uri.like(cls_name_query_str))
        triples_with_datatype = session.query(TripleObjectInferred).filter(TripleObjectInferred.subject_uri.like(cls_name_query_str))
    triples = triples.order_by(Triple.subject_uri).all()
    triples_with_datatype = triples_with_datatype.order_by(TripleObjectInferred.subject_uri).all()
    session.commit()
    # if we have a collection of triples that belong to a set of objects
    # then we need to make sure we collect whatever remaining triples these
    # objects may have
    if find_subjects:
        # throw them together...one loop instead of two
        all_triples = triples + triples_with_datatype
        # get all uris from all triples
        all_uris = [t.subject_uri for t in all_triples]
        # an uniqify
        all_uris = set(all_uris)
        for uri in all_uris:
            # just get all the associated triples!(yes, need to optimize)
            sub_triples = session.query(Triple).filter(Triple.subject_uri == uri)
            sub_triples_datatype = session.query(TripleObjectInferred).filter(TripleObjectInferred.subject_uri == uri)
            session.commit()
            # get them into a list instead of the returned sqlaclehmy datatype(trick)
            sub_triples = [ st for st in sub_triples]
            sub_triples_datatype = [ std for std in sub_triples_datatype]
            # when we add them back to the main lists, all dupes are removed automatically :)
            triples = triples + sub_triples
            triples_with_datatype = triples_with_datatype + sub_triples_datatype
    # return both lists in a tuple
    return (triples,triples_with_datatype)
    
