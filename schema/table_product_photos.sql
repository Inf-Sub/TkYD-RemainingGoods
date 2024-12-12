CREATE TABLE IF NOT EXISTS product_photos
(
    id          int auto_increment
        primary key,
    product_id  int                                 not null,
    photo_count tinyint(2)                          null comment 'Количество фото (test)',
    photo_url   varchar(255)                        not null comment 'Ссылка на фото товара',
    created_at  timestamp default CURRENT_TIMESTAMP not null,
    updated_at  timestamp default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    constraint FK_product_photos_products
        foreign key (product_id) references products (id)
            on delete cascade
)
    DEFAULT CHARSET=utf8;

