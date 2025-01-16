create table if not exists storage_locations_descriptions
(
    id                   mediumint auto_increment
        primary key,
    location_description varchar(255) null,
    constraint location_description
        unique (location_description)
)
    charset=utf8
    comment 'Описания наименований мест хранения на складах';
