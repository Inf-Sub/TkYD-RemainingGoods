create table if not exists storage_locations_names
(
    id   int auto_increment
        primary key,
    name varchar(50) not null comment 'Уникальное наименование места хранения',
    constraint unique_location_name
        unique (name)
)
    charset=utf8
    comment 'Наименования мест хранения на складах';
