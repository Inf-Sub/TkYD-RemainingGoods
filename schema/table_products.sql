CREATE TABLE IF NOT EXISTS products
(
    id            int auto_increment
        primary key,
    barcode       bigint(13)                                 not null,
    product_name  varchar(150)                               not null,
    product_width smallint(3)      default 140               null,
    product_units enum ('м', 'шт') default 'м'               not null,
    created_at    timestamp        default CURRENT_TIMESTAMP not null,
    updated_at    timestamp        default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    constraint nomenclature_number
        unique (barcode)
)
    DEFAULT CHARSET=utf8;

