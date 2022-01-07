import sqlite3

class DBHelper:
    def __init__(self, dbname="order.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def setup(self):
        stmt = "CREATE TABLE IF NOT EXISTS orders (user_id int(64), tele_handle text, location text, restaurant text, time time(0), curr_cap INT(8), capacity INT(8), PRIMARY KEY(user_id))"
        self.conn.execute(stmt)
        self.conn.commit()

    def add_item(self, user_id, tele_handle, location, restaurant, time, curr_cap, capacity):
        stmt = "INSERT INTO orders (user_id, tele_handle, location, restaurant, time, curr_cap, capacity) VALUES (?, ?, ?, ?, ?, ?, ?)"
        args = (user_id, tele_handle, location, restaurant, time, curr_cap, capacity)
        self.conn.execute(stmt, args)
        self.conn.commit()
        
    
    def delete_item(self, user_id):
        stmt = "DELETE FROM orders WHERE user_id = (?)"
        args = (user_id, )
        self.conn.execute(stmt, args)
        self.conn.commit()
    

    def get_items(self):
        stmt = "SELECT location, restaurant, time, capacity FROM items"
        return [x[0] for x in self.conn.execute(stmt)]
