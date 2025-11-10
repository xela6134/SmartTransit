#!/usr/bin/env python3

from dotenv import load_dotenv
import os, mysql.connector
from names_generator import generate_name
from random import randint
from random import uniform
from random import seed as setseed
import hashlib
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

# Determine the path to an env file
env_path = os.path.join('..', 'backend', '.env')

load_dotenv(
    dotenv_path=env_path,
    override=True
)

config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

def clear_db(cursor):
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE Users")
        cursor.execute("TRUNCATE TABLE Bookings")
        cursor.execute("TRUNCATE TABLE Operates")
        cursor.execute("TRUNCATE TABLE Rides")
        cursor.execute("TRUNCATE TABLE Locations")
        cursor.execute("TRUNCATE TABLE Drivers")
        cursor.execute("TRUNCATE TABLE Vehicles")
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        print("Database cleared!")
    except mysql.connector.Error as err:
        print(f"Failed to clear database: {err}")

def insert_locations(cursor):
    locations = [
        ('1 Utama Shopping Centre', 3.1483035750016946, 101.61639878010656),
        ('KL Sentral Bus Station Terminal', 3.134200206107094, 101.68701173963062),
        ('KLIA1 Bus Terminal', 2.7567170092173003, 101.70487259544902),
        ('Petronas Twin Towers', 3.157874187092653, 101.7115776744166),
        ('Merdeka Square', 3.149360450571316, 101.69370211079462),
        ('Batu Caves', 3.2390824210582387, 101.68409479392692),
        ('KL Tower', 3.1531548620702106, 101.70383980497463),
        ('Mid Valley Megamall', 3.1177663430341, 101.67745021079453),
        ('Pasar Malam Connaught', 3.0816628766625396, 101.73758709545027),
        ('SS15 Courtyard', 3.07814315069221, 101.5864787819583),
        ('Publika Shopping Gallery', 3.171681294478245, 101.66420009545068),
        ('IOI Mall Puchong', 3.0465505840779885, 101.61840141079422),
        ('Pasar Malam Connaught', 3.0816414500199896, 101.73758709545027),
        ('ÆON Mall Wangsa Maju', 3.202366174696186, 101.73506068883927),
        ('Melawati Mall', 3.2107841326450197, 101.74865525497495),
        ("Taman Botani Putrajaya", 2.9456905105411244, 101.69552778052814),
        ("SplashMania WaterPark", 2.8941380184914514, 101.61723825574), 
        ("Embun Resort Putrajaya", 2.901970767377098, 101.720348001138),
        ("Raja Haji FisabilillahMosque", 2.9360120541693138, 101.649241443476),
        ("Kuala Lumpur Internatinal Airport", 2.742562238864031, 101.70135254904),
        ("Xiamen University Malasia", 2.8363818888542016, 101.70438066144),
        ("Hospital Banting", 2.04855893883764, 101.50129864142178)
    ]
    cursor.executemany(
        "INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (%s, %s, %s)",
        locations
    )
    print("All locations inserted!")

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def insert_users(cursor):
    # Insert admin user first
    admin_name = "KK Leong"
    admin_email = "kk_leong@example.com"
    admin_password = "admin123"
    admin_password_hash = bcrypt.generate_password_hash(admin_password).decode('utf-8')
    admin_age = 30
    admin_phone_number = "+6512345678"
    admin_disability = 0

    cursor.execute(
        """
        INSERT INTO Users (name, password_hash, email, age, phone_number, disability)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (admin_name, admin_password_hash, admin_email, admin_age, admin_phone_number, admin_disability)
    )
    print(f"Admin user inserted with email: {admin_email} and password: {admin_password}")
    user_name = "Jeff"
    user_email = "jeff@example.com"
    user_password = "jeff123"
    user_password_hash = bcrypt.generate_password_hash(user_password).decode('utf-8')
    user_age = 30
    user_phone_number = "+61426871386"
    user_disability = 0
    cursor.execute(
        """
        INSERT INTO Users (name, password_hash, email, age, phone_number, disability)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (user_name, user_password_hash, user_email, user_age, user_phone_number, user_disability)
    )

    user_name = "AdminUser"
    user_email = "user@example.com"
    user_password = "user123"
    user_password_hash = bcrypt.generate_password_hash(user_password).decode('utf-8')
    user_age = 30
    user_phone_number = "+61426871386"
    user_disability = 0

    cursor.execute(
        """
        INSERT INTO Users (name, password_hash, email, age, phone_number, disability)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (user_name, user_password_hash, user_email, user_age, user_phone_number, user_disability)
    )




    for i in range(0,101):
        m = hashlib.sha256()
        name = generate_name(seed=i, style='capital')
        m.update(name.encode('utf-8'))
        password_hash = m.hexdigest()
        email = f"{name}@gmail.com"
        age = randint(18, 95)
        num = random_with_N_digits(8)
        phone_number = "+65" + str(num)
        disability = randint(0, 1)
        print(name, password_hash, email, age, phone_number, disability)
        cursor.execute(
            """
            INSERT INTO Users (name, password_hash, email, age, phone_number, disability)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, password_hash, email, age, phone_number, disability)
        )
                
def insert_rides(cursor):
    rides = []
    for i in range(0, 51):
        start = randint(1, 20)
        end = start
        while end == start:
            end = randint(1, 20)
        dur = uniform(10.0, 30.0)
        profir = uniform(100.0, 1000.0)
        envi = uniform(100.0, 1000.0)
        rides.append((start, end, dur, 'C', profir, envi))

        cursor.executemany("""
            INSERT INTO Rides (start_location, end_location, ride_duration, ride_status, profit, environmental)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, rides)
    print("All Rides inserted!")

def insert_bookings(cursor):
    for i in range(0,501):
        rid = randint(1, 50)
        uid = randint(1, 100)
        if i % 4 == 0:
            cursor.execute("""
                INSERT INTO Bookings (ride_id, user_id, ride_date) VALUES (%s, %s, "2025-03-01")
            """,  (int(rid), int(uid))
            )
        if i % 4 == 1:
            cursor.execute("""
                INSERT INTO Bookings (ride_id, user_id, ride_date) VALUES (%s, %s, "2025-03-02")
            """,  (int(rid), int(uid))
            )
        if i % 4 == 2:
            cursor.execute("""
                INSERT INTO Bookings (ride_id, user_id, ride_date) VALUES (%s, %s, "2025-03-03")
            """,  (int(rid), int(uid))
            )
        if i % 4 == 3:
            cursor.execute("""
                INSERT INTO Bookings (ride_id, user_id, ride_date) VALUES (%s, %s, "2025-03-04")
            """,  (int(rid), int(uid))
            )
    print("All Bookings inserted!")

             

def get_db_connection():
    return mysql.connector.connect(**config)

def main():
    print("This script will remove all data from the database and add new RANDOM data")
    print("Data added will be Users, Locations, complete Rides and Bookings")
    print("You will still need to register Vehicles, Drivers and assign Drivers to Vehicles via Operates")

    res = input("Would you like to run this script? Enter Y/N: ")
    if res != "Y":
        print("Exiting script...")
        exit(0)

    seed = input("Enter an integer number to use as the random seed: ")
    setseed(seed)
    
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)
    
    try:
        clear_db(cursor)
        insert_locations(cursor)
        insert_users(cursor)
        insert_rides(cursor)
        insert_bookings(cursor)
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Failed to insert tuples: {err}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
