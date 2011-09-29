from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import Sequence

"""
Collection of helper methods that interface directly with
SQLAlchemy session. Can be used by any other package as required.
"""

def create_session(engine):
    """
    Initializes the SQLAlchemy session.
    
    engine - the SQLAlchemy engine
    """
    Session = scoped_session(sessionmaker(bind=engine))
    # declare session at module scope for easy access
    session = Session()
    return session

def get_id(session):
    """
    Retrieves the next id reserved for the triples table.
    
    session - the current SQLAlchemy session
    """
    sequence = Sequence("triple_id_seq")
    next_id = session.connection().execute(sequence)
    return next_id
