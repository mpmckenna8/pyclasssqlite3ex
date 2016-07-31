# lets us use the context manager
# https://docs.python.org/2/library/contextlib.html
from contextlib import closing, contextmanager

import sqlite3
from threading import Lock

FILENAME = "polygoners.sqlite"
TABLE_NAME = "polygons"



class Polygon(object):
    """Represents a polygon holding (pkey, name, sides and sides_english)"""
    # don't have to worry about the
    def __init__(self, pkey=0, name='', sides='', sides_english=''):
#think sqlite will take care of the key field automatically
        self.pkey = pkey
        self.name = name
        self.sides = sides
        self.sides_english = sides_english


    @classmethod
    def from_row(cls, row):
        return Polygon(*row)



class PolygonDB(object):
    def __init__(self):
              ## 1. ADD check_same_thread... otherwise Python will complain.
        ## This allows us to use multiple threads on the same connection. Be sure to have sqlite built with
        ## the Serialized option (default) and version 3.3.1 or later.
        ## 2. Change the isolation level to deferred so we can control transactions
        self._connection = sqlite3.connect( FILENAME, check_same_thread=False, isolation_level='DEFERRED' )
                ## WAL requires SQLite version 3.7 or later. SO make sure you have that
        self._connection.execute('PRAGMA journal_mode = WAL')
        self._lock = Lock()

    def create_table(self):
        """ Creating our polygons table """
        with closing(self._connection.cursor()) as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS " + TABLE_NAME + " ( pkey INTEGER PRIMARY KEY, name text, sides INTEGER, sides_english text)")


#example of code vulnerable to injection
    # This is vulnerable to injection. DO NOT execute statements where the string is built from user input
    # def insert(self, stock):
    #     """Insert stock in DB"""
    #     keys = stock.__dict__.iterkeys()
    #     values = (sql_value(x) for x in stock.__dict__.itervalues())
    #     with closing(self._connection.cursor()) as cursor:
    #         cursor.execute("INSERT INTO stocks({}) VALUES ({})".format(", ".join(keys), ", ".join(values)))

    def insert(self, poly):
        # insert poly (Polygon) into db if it doesn't already exist
        ## Note this is using prepared statement format so it is safe from injection
        places = ','.join(['?']*len(poly.__dict__))

        keys = ','.join(poly.__dict__.iterkeys())
        values = tuple(poly.__dict__.itervalues())

        with closing(self._connection.cursor()) as cursor:
            cursor.execute("INSERT INTO " + TABLE_NAME + "({}) VALUES ({})".format(keys, places), values)

    def lookup(self, name):
        """ Look up a stock if found else none """
        print 'made it here'
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('SELECT * FROM ' + TABLE_NAME + ' where name= ?', (name,))
            row =  cursor.fetchone()

        #if you try to mess up with the cursor not in the block above it won't let you b/c it closes it
        #row = cursor.fetchone()
        if row:
            print row
            # because I have that
            return Polygon.from_row( row )#(row[1], row[2], row[3]))


    def update(self, poly):
        """ update the values of an existing stock """
        updates = ','.join(key + ' = ?' for key in poly.__dict__.iterkeys())
        print updates
        print "updates above values below "
        values = tuple(poly.__dict__.values() + [poly.name])
        print values
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('UPDATE polygons SET {} WHERE name = ?'.format(updates), values)
        print ('UPDATE polygons SET {} WHERE name = ?'.format(updates), values)
    # This is ok if each thread has its own connection. The writes will be serialized by SQLite
    # I recommend sharing connections (below) because it it makes bookkeeping easier. If you do go with a separate
    # connection per thread, consider overriding Thread.Run so you close the connection when Run completes.
    # Otherwise, your unittests can have a hard time creating and deleting lots of temporary databases.
    # def transaction(self):
    #     return self._connection

    # This allows threads to share connections. When multiple threads are writing we perform the serialization
    # by holding self._lock. No performance penalty here from our lock because SQLite only allows one writer at time anyways.
    @contextmanager
    def transaction(self):
        with self._lock:
            try:
                yield
                self._connection.commit()
            except:
                self._connection.rollback()
                raise






#example/ test functions

def main():
    db = PolygonDB()
    db.create_table()
    polyer = Polygon(None, "triangle", 3, "trienglish")
    with db.transaction():
        db.insert(polyer)

    poly2 = Polygon(None, "square", 4, "squizare")
    with db.transaction():
        db.insert(poly2)



def updateSquare():
    db = PolygonDB()
    newsq = Polygon( None, "square", 4, "squarezee")
    with db.transaction():
        db.update(newsq)

def lookupTriangle():
    db = PolygonDB()
    with db.transaction():
        looktri = db.lookup("triangle")
        print looktri.name




#calling some text functions
if __name__  == "__main__":
#    main()
#    updateSquare()
    lookupTriangle()
