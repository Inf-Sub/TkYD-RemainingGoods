create table product_quantity
(
    id           int auto_increment
        primary key,
    product_id   int                                              not null,
    warehouse_id smallint(3)                                      not null,
    quantity     decimal(7, 3) unsigned default 0.000             not null comment 'Количество на складе',
    created_at   timestamp              default CURRENT_TIMESTAMP not null,
    updated_at   timestamp              default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    constraint FK_product_quantity_products
        foreign key (product_id) references products (id),
    constraint FK_product_quantity_warehouses
        foreign key (warehouse_id) references warehouses (id)
)
    comment 'Количество товара';

