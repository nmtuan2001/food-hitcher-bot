import sqlite3
import geopy.distance

class DBHelper:
    def __init__(self, dbname="order.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def setup(self):
        stmt = "CREATE TABLE IF NOT EXISTS orders (user_id int(64), tele_handle text, location text, lat int(32), lng int(32), restaurant text, time time(0), curr_cap INT(8), capacity INT(8), PRIMARY KEY(user_id))"
        self.conn.execute(stmt)
        self.conn.commit()

    def add_item(self, user_id, tele_handle, location, lat, lng, restaurant, time, curr_cap, capacity):
        stmt = "INSERT INTO orders (user_id, tele_handle, location, lat, lng, restaurant, time, curr_cap, capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        args = (user_id, tele_handle, location, lat, lng, restaurant, time, curr_cap, capacity)
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

    def search_user(self, user_id):
        stmt = "SELECT EXISTS(SELECT 1 FROM orders WHERE user_id=(?))"
        args = (user_id, )
        return self.conn.execute(stmt, args).fetchone()

    def distance(lat1, lng1, lat2, lng2):
        coord1 = (lat1, lng1)
        coord2 = (lat2, lng2)
        return geopy.distance.distance(coord1, coord2).km
    
    def closest_items(self, lat, lng):
        stmt = "SELECT * FROM orders"
        closest = []
        for order in [x for x in self.conn.execute(stmt)]:
            distance_from = DBHelper.distance(lat, lng, order[3], order[4])
            new_order = []
            new_order.append(distance_from)
            new_order = new_order + list(order)
            closest.append(new_order)
        return sorted(closest, key = lambda x: x[0])[:5]