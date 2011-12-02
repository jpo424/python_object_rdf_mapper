from sqlalchemy import create_engine,Table, Column, Integer, String, MetaData, Sequence
from sqlalchemy.orm import mapper
from lib import create_session
import models

"""
Initializes all state required for SQL system
including SQLAlchemy system
"""

# init all state for this package
def initialize(connect_string):
    """
    Initializes package state/ SQLAlchemy session state 
    
    connect_string - SQLAlchemy engine configuration string
    """
    print("Initializing SQL Manager")
    return initialize_triple_store(connect_string)

# create the triple store if it is not already created
# accepts standard sqlalchemy connect string(db+dialect//credentials)
def initialize_triple_store(connect_string):
    """
    Does the Actual Initializations.
    Configures SQLAlchemy engine and creates
    triple store if it does not exist
    
    connect_string - SQLAlchemy engine configuration string
    """
    engine = create_engine(connect_string, echo=True)
    metadata = MetaData()
    # create tables for triple store
    triples_table = Table('triples', metadata,
        # explicit sequence directive for oracle db
        Column('id', Integer, Sequence('triple_id_seq'), primary_key=True),
        # columns for URIs
        Column('subject_uri', String(255)),
        Column('predicate_uri', String(255)),
        Column('object_uri', String(255)),
        sqlite_autoincrement = True
        )
    triples_object_inferred_table = Table('triples_object_inferred', metadata,
        Column('id', Integer, Sequence('triple_object_id_seq'), primary_key=True),
        # columns for URIs
        Column('subject_uri', String(255)),
        Column('predicate_uri', String(255)),
        # polymorphic value column
        Column('object_type', String(255)),
        Column('object_value', String(255)),
        sqlite_autoincrement = True
        )
    # create the tables(if they dont already exist)
    metadata.create_all(engine)
    # bind model classes to tables
    mapper(models.Triple, triples_table)
    mapper(models.TripleObjectInferred,triples_object_inferred_table)
    session = create_session(engine)
    return session
    
