#!/usr/bin/env python3

from dotenv import load_dotenv
import os, mysql.connector, pprint

# Determine the path to an env file
env_path = os.path.join('..', 'backend', '.env.test')
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

def insert_locations(cursor):
    locations = [
        ('1 Utama Shopping Centre', 3.1483035750016946, 101.61639878010656),
        ('KL Sentral Bus Station Terminal', 3.134200206107094, 101.68701173963062),
        ('KLIA1 Bus Terminal', 2.7567170092173003, 101.70487259544902),
        ('Petronas Twin Towers', 3.157874187092653, 101.7115776744166),
        ('Merdeka Square', 3.149360450571316, 101.69370211079462),
        # ('Batu Caves', 3.2390824210582387, 101.68409479392692),
        # ('KL Tower', 3.1531548620702106, 101.70383980497463),
        # ('Mid Valley Megamall', 3.1177663430341, 101.67745021079453),
        # ('Pasar Malam Connaught', 3.0816628766625396, 101.73758709545027),
        # ('SS15 Courtyard', 3.07814315069221, 101.5864787819583),
        # ('Publika Shopping Gallery', 3.171681294478245, 101.66420009545068),
        # ('IOI Mall Puchong', 3.0465505840779885, 101.61840141079422),
        # ('Pasar Malam Connaught', 3.0816414500199896, 101.73758709545027),
        # ('ÆON Mall Wangsa Maju', 3.202366174696186, 101.73506068883927),
        # ('Melawati Mall', 3.2107841326450197, 101.74865525497495),
    ]
    try:
        cursor.executemany(
            "INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (%s, %s, %s)",
            locations
        )
        print("All locations inserted")
    except mysql.connector.Error as err:
        print(f"Failed to insert locations: {err}")

def get_db_connection():
    return mysql.connector.connect(**config)

def main():
    print("Starting dB query script...")

    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)
    
    # insert_locations(cursor)
    # conn.commit()

    user_input = input("Enter a query you want to execute (type 'exit' to stop): ")
    while user_input.lower() != 'exit':
        try:
            cursor.execute(user_input)
            conn.commit()
            print("Query was successful!")
            pprint.pp(cursor.fetchall())
        except mysql.connector.Error as err:
            print(f"Query failed: {err}")
            conn.rollback()
        user_input = input("Enter a query you want to execute (type 'exit' to stop): ")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
