CREATE TABLE IF NOT EXISTS storage_location_names
(
    id   int auto_increment
        primary key,
    name varchar(50) not null comment 'Уникальное наименование места хранения',
    constraint unique_location_name
        unique (name)
)
    DEFAULT CHARSET=utf8
    comment 'Уникальные Наименования Мест Хранения';
