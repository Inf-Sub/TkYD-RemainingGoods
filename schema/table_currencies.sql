create table currencies
(
    id            tinyint(1) auto_increment
        primary key,
    currency_code char(3) not null comment 'Код валюты, например, USD, RUB',
    constraint currency_code
        unique (currency_code)
);

