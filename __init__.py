import sql_manager
import triple_manager
import object_manager

"""
initialize the environment
calls initialize in each package
initializes any required state
"""

def initialize(connect_string):
    """
    Initializes the rdf Mapper system, most importantly the SQL session
    connect_string - SQLAlchemy engine configuration string     
    """
    print("Initializing RDF Mapper Environment")
    session = sql_manager.initialize(connect_string)
    # set session on super class to newly instantiated db session
    # now all RDFSubject sub classes have easy access to session
    object_manager.models.RDFSubject._session = session
    return session
