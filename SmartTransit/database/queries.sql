create table if not exists Locations (
    location_id     bigint not null auto_increment,
    location_name   varchar(80),
    x_coordinate    decimal(15,12),
    y_coordinate    decimal(15,12),
    primary key (location_id)
);

create table if not exists Users (
    user_id         bigint not null auto_increment,
    name            varchar(80) not null,
    password_hash   varchar(255) not null,
    email           varchar(250) not null,
    age             integer,
    disability      boolean,
    location        decimal(15,12),
    flag            char(1),
    primary key (user_id),
    check (flag in ('U', 'A', 'D'))
);

create table if not exists Rides (
    ride_id         bigint not null auto_increment,
    start_location  bigint,
    end_location    bigint,
    ride_duration   float,
    ride_started    boolean,
    ride_finished   boolean,
    vehicle_id      bigint,
    profit          float,
    primary key (ride_id),
    foreign key (start_location) references Locations(location_id),
    foreign key (end_location) references Locations(location_id),
    foreign key (vehicle_id) references Vehicles(vehicle_id),
);

create table if not exists Bookings (
    ride_id         bigint,
    user_id         bigint,
    ride_date       datetime not null,
    foreign key (ride_id) references Rides(ride_id),
    foreign key (user_id) references Users(user_id)
);

create table if not exists Vehicle (
    vehicle_id      bigint not null auto_increment,
    on_transit      boolean,
    x_coordinate    decimal(15,12),
    y_coordinate    decimal(15,12),
    primary key (vehicle_id),
);    

create table if not exists RevokedTokens (
    jti         varchar(36),
    expires_at  datetime not null,
    index (expires_at),
    primary key (jti)
);
