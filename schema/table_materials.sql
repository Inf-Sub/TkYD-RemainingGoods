create table materials
(
    id                   tinyint(3) auto_increment
        primary key,
    material_name        varchar(25)                         not null comment 'Название материала',
    material_description varchar(150)                        not null,
    created_at           timestamp default CURRENT_TIMESTAMP not null,
    updated_at           timestamp default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    constraint material_name
        unique (material_name)
);

