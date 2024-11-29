create table warehouses
(
    id                   smallint(3) auto_increment
        primary key,
    internal_number      smallint(3) unsigned zerofill default 0                 not null,
    warehouse_short_name char(8)                                                 not null,
    warehouse_name       varchar(100)                                            not null,
    currency_id          tinyint(1)                    default 2                 not null,
    created_at           timestamp                     default CURRENT_TIMESTAMP not null,
    updated_at           timestamp                     default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    constraint warehouse_short_name
        unique (warehouse_short_name),
    constraint FK_warehouses_currencies
        foreign key (currency_id) references currencies (id)
);




