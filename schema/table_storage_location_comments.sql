CREATE TABLE IF NOT EXISTS storage_location_comments
(
    location_id    int       not null,
    description_id mediumint not null,
    primary key (location_id, description_id),
    constraint FK_storage_location_comments_storage_location_descriptions
        foreign key (description_id) references storage_location_descriptions (id)
            on update cascade,
    constraint FK_storage_location_comments_storage_location_names
        foreign key (location_id) references storage_location_names (id)
            on update cascade
)
    DEFAULT CHARSET=utf8;

