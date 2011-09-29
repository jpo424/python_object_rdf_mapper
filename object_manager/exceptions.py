"""
RDF Model Exceptions
"""

class RDFException(Exception):
    """
    Super class of all RDF Model exceptions
    """
    
    def __init__(self):
        self.error_cause = "RDFException error cause"
    
    def __str__(self):
        return self.error_cause
        
class RDFNoUriException(RDFException):
    """
    Exception raised when an object is missing a URI value.
    Usually, during the saving process, this exception can be rasied
    on both RDFSubject objects or their owned objects.
    """
    
    URI_ERRORS = {1:"URI Not Defined for Class.", 2:"URI Value None for predicate: ", 3:"URI value cannot be list or tuple"}
    
    def __init__(self, error_obj,error_val=None):
        if error_val:
            self.error_cause = self.URI_ERRORS.get(error_val)
        else:
            # determine error cause
            error = None
            pred_names = error_obj.__class__.predicates
            for pred_name in pred_names:
                class_pred_val = error_obj.__class__.__dict__[pred_name]
                if class_pred_val.is_uri:
                    error = self.URI_ERRORS.get(2) + pred_name
            if error == None:
                error = self.URI_ERRORS.get(1)
            self.error_cause = error

class RDFObjectNoUriException(RDFNoUriException):
    """
    Exception rasied when an RDFSubject's object is lacking a uri during
    the find or save process...becuase there is no uri attribute or the uri
    val is None
    """
    URI_ERRORS = {1:"Object URI Not Defined.", 2:"Object URI Value None for predicate: "}
    
class RDFDeletionException(RDFException):
    """
    Exception raised when there is a problem with deleting an object.
    Normally when it was never saved in the first place or referenced elsewhere. 
    """
    
    ERRORS = {1:"Cannot delete object, No URI Assigned", 2:"Cannot delete object, it is being referenced by another Subject", 3:""}
    
    def __init__(self,error_val):
        self.error_cause = self.ERRORS.get(error_val)

class RDFObjectPersistanceException(RDFException):
    """
    Exception raised when an RDFSubject's object has not been saved yet or
    is simply not a RDFMapper compatible object 
    """
    ERRORS = {1:"RDF Object is not in DB", 2:"Object Class type cannot be found in graph/ does not inherit from RDFSubject"}
    
    def __init__(self,error_val):
        self.error_cause = self.ERRORS.get(error_val)
        
    