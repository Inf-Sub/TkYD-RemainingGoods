CREATE TABLE IF NOT EXISTS product_materials
(
    id            int auto_increment
        primary key,
    product_id    int                                                not null,
    material_id   tinyint unsigned zerofill                          not null,
    material_type enum ('main', 'coating') default 'main'            not null comment 'Тип состава: основной или покрытие',
    proportion    decimal(5, 2)                                      not null comment 'Процент материала в составе ткани',
    created_at    timestamp                default CURRENT_TIMESTAMP not null,
    updated_at    timestamp                default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    constraint product_id_material_id
        unique (product_id, material_id, material_type),
    constraint FK_product_materials_materials
        foreign key (material_id) references materials (id)
            on update cascade,
    constraint FK_product_materials_products
        foreign key (product_id) references products (id)
            on update cascade
)
    DEFAULT CHARSET=utf8;

