create table product_prices
(
    id                  int auto_increment
        primary key,
    product_quantity_id int                                  not null,
    price               decimal(5, 2)                        not null comment 'Цена товара на складе',
    currency_id         tinyint(1) default 2                 not null,
    created_at          timestamp  default CURRENT_TIMESTAMP not null,
    updated_at          timestamp  default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    constraint FK_product_prices_currencies
        foreign key (currency_id) references currencies (id),
    constraint FK_product_prices_product_quantity
        foreign key (product_quantity_id) references product_quantity (id)
            on delete cascade
);



