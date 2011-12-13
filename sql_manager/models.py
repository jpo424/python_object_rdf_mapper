
"""
 The SQLAlchemy Models that serve as the interface
 to the triple store tables
"""
class Triple(object):
    
    """
    Representation of a standard triple
    where each Sub,Pred,Obj has a URI
    """

    def __str__(self):
        string_rep = "Subject:{0}, Predicate:{1}, Object:{2}"
        return string_rep.format(self.subject_uri, self.predicate_uri, self.object_uri)


class TripleWithDatatype(object):
    
    """
    Representation of a triple where object
    does not have a URI(no graph schema backing).
    Usually, will represent triples where the object
    value is a native Python data type
    """
    
    def __str__(self):
        string_rep = "Subject:{0}, Predicate:{1}, ObjectType:{2}, ObjectValue:{3}"
        return string_rep.format(self.subject_uri, self.predicate_uri, self.object_type, self.object_value)
        