create table if not exists storage_locations_comments
(
    location_id    int       not null,
    description_id mediumint not null,
    primary key (location_id, description_id),
    constraint FK_storage_locations_comments_storage_locations_descriptions
        foreign key (description_id) references storage_locations_descriptions (id)
            on update cascade,
    constraint FK_storage_locations_comments_storage_locations_names
        foreign key (location_id) references storage_locations_names (id)
            on update cascade
)
    charset=utf8
    comment 'Таблица взаимосвязей имен мест хранения и их описаний';
