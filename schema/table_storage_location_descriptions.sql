create table storage_location_descriptions
(
    id                   mediumint auto_increment
        primary key,
    location_description varchar(255) null,
    constraint location_description
        unique (location_description)
);

