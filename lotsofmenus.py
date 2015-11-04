from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Parent, Base, Child

engine = create_engine('sqlite:///parentchild.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

skishop1 = Parent(name="Mountain Hut")
session.add(skishop1)
session.commit()

item1 = Child(name="Tutle Neck", description="Neck armour",
              price="$10.00", attribute="For purchase", parent=skishop1)

session.add(item1)
session.commit()

item2 = Child(name="Banana Ride", description="Yellow Ski board",
              price="$200.00", attribute="For purchase", parent=skishop1)

session.add(item2)
session.commit()

item2 = Child(name="volks1100", description="Cross country skis",
              price="$350.00", attribute="For purchase and rental", parent=skishop1)

session.add(item2)
session.commit()

skishop2 = Parent(name="Blue Bar")
session.add(skishop2)
session.commit()

item21 = Child(name="Pumpkin Ale", description="Draught Beer of the season",
              price="$5.00", attribute="For purchase", parent=skishop2)

session.add(item21)
session.commit()

skishop3 = Parent(name="Midway Stop")
session.add(skishop3)
session.commit()



print "added menu items!"
