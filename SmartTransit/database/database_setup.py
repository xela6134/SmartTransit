from dotenv import load_dotenv
import os, mysql.connector

# Determine the path to an env file 
env_path = os.path.join('..', 'backend', '.env.test')
load_dotenv(
    dotenv_path=env_path,
    override=True
)

create_locations_query = """
create table if not exists Locations (
    location_id     bigint not null auto_increment,
    location_name   varchar(80),
    x_coordinate    decimal(15,12),
    y_coordinate    decimal(15,12),
    primary key (location_id)
);
"""

create_users_query = """
create table if not exists Users (
    user_id         bigint not null auto_increment,
    name            varchar(80),
    password_hash   varchar(255),
    email           varchar(250),
    age             integer,
    sex             char(1),
    phone_number    varchar(20),
    disability      boolean,
    location        decimal(15,12),
    primary key (user_id),
    check (sex in ('M', 'F', 'O')) -- Male, Female, Other
);
"""

create_table_rides = """
create table if not exists Rides (
    ride_id         bigint not null auto_increment,
    start_location  bigint,
    end_location    bigint,
    ride_duration   float,
    ride_status     char(1),
    profit          float,
    environmental   float,
    primary key (ride_id),
    foreign key (start_location) references Locations(location_id),
    foreign key (end_location) references Locations(location_id),
    check (ride_status in ('I', 'A', 'C')) -- Inactive, Active, Complete
);
"""

create_table_operates = """
create table if not exists Operates (
    driver_id       bigint,
    ride_id         bigint,
    foreign key (driver_id) references Drivers(driver_id),
    foreign key (ride_id) references Rides(ride_id)
);
"""

create_table_drivers = """
create table if not exists Drivers (
    driver_id           bigint not null auto_increment,
    assigned_vehicle    bigint,
    name                varchar(80),
    age                 integer,
    email               varchar(250),
    password_hash       varchar(255),
    employee_type       char(1),
    driver_salary       float,
    hire_date           date,
    primary key         (driver_id),
    foreign key (assigned_vehicle) references Vehicles(vehicle_id),
    check (employee_type in ('C', 'P', 'F')) -- Casual, Part-Time, Full-Time
);
"""

create_table_bookings = """
create table if not exists Bookings (
    ride_id         bigint,
    user_id         bigint,
    ride_date       datetime not null,
    foreign key (ride_id) references Rides(ride_id),
    foreign key (user_id) references Users(user_id)
);
"""

create_table_vehicles = """
create table if not exists Vehicles (
    vehicle_id          bigint not null auto_increment,
    capacity            integer,
    disability_seats    integer,
    x_coordinate        decimal(15,12),
    y_coordinate        decimal(15,12),
    licence_number      varchar(8),
    primary key (vehicle_id)
); 
"""

create_revoked_tokens_query = """
create table if not exists RevokedTokens (
    jti         varchar(36),
    expires_at  datetime not null,
    index (expires_at),
    primary key (jti)
);
"""

create_SMS_tokens = """
CREATE TABLE IF NOT EXISTS SmsTokens (
    email           varchar(250),
    token           varchar(8),
    expires_at  datetime not null,
    active          boolean
)

"""


config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

def get_db_connection():
    return mysql.connector.connect(**config)

def main():
    conn = get_db_connection()
    cursor = conn.cursor()

    queries = [
        create_locations_query,
        create_table_vehicles,
        create_users_query,
        create_table_rides,
        create_table_bookings,
        create_revoked_tokens_query,
        create_table_drivers,
        create_table_operates,
        create_SMS_tokens
    ]
    
    try:
        for query in queries:
            cursor.execute(query)
        conn.commit()
        print("Tables created successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()