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
    # explicit workaround for sqlite
    # get the last id used, add 1 to it(use it)
    # update table with sequence + 1
    engine_text = str(session.bind.engine)
    if 'sqlite' in engine_text:
        next_id = session.connection().execute("select seq from sqlite_sequence where name = 'triples';").first()[0]
        next_id = next_id + 1
        update_text = "update sqlite_sequence set seq = {0} where name = 'triples'".format(next_id)
        # increment the sequence table value so we do use id again
        session.connection().execute(update_text)
    else:
        sequence = Sequence("triple_id_seq")
        next_id = session.connection().execute(sequence)
    return next_id
