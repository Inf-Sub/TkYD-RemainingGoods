create table storage_locations
(
    id               int auto_increment
        primary key,
    product_quantity_id         int                                 not null,
    location_name_id int                                 null,
    created_at       timestamp default CURRENT_TIMESTAMP not null,
    updated_at       timestamp default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    constraint FK_storage_locations_stock
        foreign key (product_quantity_id) references product_quantity (id)
            on delete cascade,
    constraint FK_storage_locations_storage_location_names
        foreign key (location_name_id) references storage_location_names (id)
            on delete cascade
)
    comment 'Место Хранения';

