create table if not exists products_on_warehouses
(
    id           int auto_increment
        primary key,
    product_id   int                                              not null,
    warehouse_id smallint(3)                                      not null,
    price        decimal(8, 2)                                    not null comment 'Цена товара на складе',
    quantity     decimal(8, 2) unsigned default 0.00              not null comment 'Количество на складе',
    created_at   timestamp              default CURRENT_TIMESTAMP not null,
    updated_at   timestamp              default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    constraint product_id_warehouse_id
        unique (product_id, warehouse_id),
    constraint FK_products_on_warehouses_products
        foreign key (product_id) references products (id)
            on delete cascade,
    constraint FK_products_on_warehouses_warehouses
        foreign key (warehouse_id) references warehouses (id)
            on delete cascade
)
    charset=utf8
    comment 'Количество товара на складах';
