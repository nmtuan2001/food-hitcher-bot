import sqlite3


class DBHelper:
    def __init__(self, dbname="order.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def setup(self):
        stmt = "CREATE TABLE IF NOT EXISTS orders (location text, restaurant text, time time(0), curr_cap INT(8), capacity INT(8))"
        self.conn.execute(stmt)
        self.conn.commit()

    def add_item(self, location, restaurant, time, capacity):
        stmt = "INSERT INTO orders (location, restaurant, time, capacity) VALUES (?, ?, ?, ?)"
        args = (location, restaurant, time, capacity)
        self.conn.execute(stmt, args)
        self.conn.commit()
        
    """
    def delete_item(self, id_no):
        stmt = "DELETE FROM orders WHERE id = (?)"
        args = (id_no, )
        self.conn.execute(stmt, args)
        self.conn.commit()
    """

    def get_items(self):
        stmt = "SELECT location, restaurant, time, capacity FROM items"
        return [x[0] for x in self.conn.execute(stmt)]
