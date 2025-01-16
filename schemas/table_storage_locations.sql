create table if not exists storage_locations
(
    id                 int auto_increment
        primary key,
    storage_product_id int                                 not null,
    location_name_id   int                                 null,
    created_at         timestamp default CURRENT_TIMESTAMP not null,
    updated_at         timestamp default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    constraint FK_storage_locations_storage_locations_names
        foreign key (location_name_id) references storage_locations_names (id)
            on delete cascade,
    constraint FK_storage_locations_products_on_warehouses
        foreign key (storage_product_id) references products_on_warehouses (id)
            on delete cascade
)
    charset = utf8
    comment 'Места Хранения товара на складах';

# create index FK_storage_locations_product_price_and_quantity
#     on storage_locations (storage_product_id);
