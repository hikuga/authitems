from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Parent, Base, Child

engine = create_engine('sqlite:///parentchild.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

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

item22 = Child(name="Iron Monkey", description="Draught Beer",
               price="$5.00", attribute="For purchase", parent=skishop2)

session.add(item22)
session.commit()

skishop3 = Parent(name="Midway Stop")
session.add(skishop3)
session.commit()



print "added menu items!"
