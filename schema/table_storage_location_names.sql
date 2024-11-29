create table storage_location_names
(
    id   int auto_increment
        primary key,
    name varchar(10) not null comment 'Уникальное наименование места хранения',
    constraint unique_location_name
        unique (name)
)
    comment 'Уникальные Наименования Мест Хранения';

