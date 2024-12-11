create table storage_product
(
    id           int auto_increment
        primary key,
    product_id   int                                              not null,
    warehouse_id smallint(3)                                      not null,
    price        decimal(6, 2)                                    not null comment 'Цена товара на складе',
    quantity     decimal(7, 3) unsigned default 0.000             not null comment 'Количество на складе',
    created_at   timestamp              default CURRENT_TIMESTAMP not null,
    updated_at   timestamp              default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    constraint product_id_warehouse_id
        unique (product_id, warehouse_id),
    constraint FK_storage_product_products
        foreign key (product_id) references products (id)
            on delete cascade,
    constraint FK_storage_product_warehouses
        foreign key (warehouse_id) references warehouses (id)
            on delete cascade
)
    comment 'Количество товара';



