CREATE TABLE IF NOT EXISTS storage_locations
(
    id                 int auto_increment
        primary key,
    storage_product_id int                                 not null,
    location_name_id   int                                 null,
    created_at         timestamp default CURRENT_TIMESTAMP not null,
    updated_at         timestamp default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    constraint FK_storage_locations_storage_location_names
        foreign key (location_name_id) references storage_location_names (id)
            on delete cascade,
    constraint FK_storage_locations_storage_product
        foreign key (storage_product_id) references storage_product (id)
            on delete cascade
)
    DEFAULT CHARSET=utf8
    comment 'Место Хранения';

create index FK_storage_locations_product_price_and_quantity
    on storage_locations (storage_product_id);



