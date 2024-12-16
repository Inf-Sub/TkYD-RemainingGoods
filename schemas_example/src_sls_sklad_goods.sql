-- --------------------------------------------------------
-- Хост:                         127.0.0.1
-- Версия сервера:               5.6.51-log - MySQL Community Server (GPL)
-- Операционная система:         Win64
-- HeidiSQL Версия:              12.8.0.6908
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Дамп структуры базы данных sls_sklad_goods
CREATE DATABASE IF NOT EXISTS `sls_sklad_goods` /*!40100 DEFAULT CHARACTER SET utf8 */;
USE `sls_sklad_goods`;

-- Дамп структуры для таблица sls_sklad_goods.currencies
CREATE TABLE IF NOT EXISTS `currencies` (
  `id` tinyint(1) NOT NULL AUTO_INCREMENT,
  `currency_code` char(3) NOT NULL COMMENT 'Код валюты, например, USD, RUB',
  PRIMARY KEY (`id`),
  UNIQUE KEY `currency_code` (`currency_code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

-- Дамп данных таблицы sls_sklad_goods.currencies: ~2 rows (приблизительно)
INSERT INTO `currencies` (`id`, `currency_code`) VALUES
	(2, 'RUB'),
	(1, 'USD');

-- Дамп структуры для таблица sls_sklad_goods.materials
CREATE TABLE IF NOT EXISTS `materials` (
  `id` tinyint(3) NOT NULL AUTO_INCREMENT,
  `material_name` varchar(25) NOT NULL COMMENT 'Название материала',
  `material_description` varchar(150) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `material_name` (`material_name`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8;

-- Дамп данных таблицы sls_sklad_goods.materials: ~19 rows (приблизительно)
INSERT INTO `materials` (`id`, `material_name`, `material_description`, `created_at`, `updated_at`) VALUES
	(1, 'Хлопок', 'Хлопок - натуральная ткань, получаемая из растительного сырья - хлопчатника. Из волокон получают ткань и нити, вату.', '2024-10-09 21:42:05', '2024-10-09 22:36:34'),
	(2, 'Полиэстер', '', '2024-10-09 21:42:05', '2024-10-09 21:42:05'),
	(3, 'Эластан', 'Волокна обладают высокой растяжимостью (при деформации длина нити увеличивается в 2-3 раза) и пластичностью.', '2024-10-09 21:57:04', '2024-10-09 22:31:22'),
	(4, 'Полиамид', 'Синтетические волокна, получаемые в результате химической переработки нефти, угля, природного газа.', '2024-10-09 22:03:38', '2024-10-09 22:31:28'),
	(5, 'Акрил', '', '2024-10-09 22:03:48', '2024-10-09 22:03:48'),
	(6, 'Вискоза', '', '2024-10-09 22:04:32', '2024-10-09 22:04:32'),
	(7, 'Шерсть', '', '2024-10-09 22:04:54', '2024-10-09 22:04:54'),
	(8, 'Нейлон', 'Легкий, быстро сохнущий, яркий и упругий текстиль. Его сложно разорвать, повредить. Ниточка нейлона гладкая, ровная и приглушенно-блестящая.', '2024-10-09 22:05:13', '2024-10-09 22:31:33'),
	(9, 'Кашемир', '', '2024-10-09 22:05:40', '2024-10-09 22:05:40'),
	(10, 'Ацетат', '', '2024-10-09 22:06:23', '2024-10-09 22:06:23'),
	(11, 'Люрекс', 'Нить в виде узкой полоски блестящей (покрытой фольгой или металлизированной) плёнки, вплетаемая в ткань для её украшения.', '2024-10-09 22:06:59', '2024-10-09 22:31:39'),
	(12, 'Шелк', 'Натуральное волокно, знаменитое своей прочностью и долговечностью, получаемое из коконов тутового шелкопряда, состоит из белков фиброина и серицина.', '2024-10-09 22:07:18', '2024-10-09 22:33:30'),
	(13, 'Резиновая нить', '', '2024-10-09 22:08:02', '2024-10-09 22:08:02'),
	(14, 'Лен', 'Волокно, полученное в результате обработки стеблей льна.', '2024-10-09 22:09:02', '2024-10-09 22:37:24'),
	(15, 'Полиуретан', '', '2024-10-09 22:10:17', '2024-10-09 22:10:17'),
	(17, 'Шерсть альпака', '', '2024-10-09 22:13:40', '2024-10-09 22:13:40'),
	(19, 'Шерсть вирджиния', '', '2024-10-09 22:14:32', '2024-10-09 22:14:32'),
	(20, 'Полиакрил', '', '2024-10-09 22:16:13', '2024-10-09 22:16:13'),
	(21, 'Прочие волокна', 'Прочие синтетические волокна.', '2024-10-09 22:17:28', '2024-10-09 22:31:26'),
	(22, 'Лен Рами', 'Экологически чистая ткань из волокон крапивы. Это прочный фактурный материал с серебристым отливом.', '2024-10-09 23:24:17', '2024-10-09 23:28:44');

-- Дамп структуры для таблица sls_sklad_goods.products
CREATE TABLE IF NOT EXISTS `products` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `barcode` bigint(13) NOT NULL,
  `product_name` varchar(150) NOT NULL,
  `product_width` smallint(3) DEFAULT '140',
  `product_units` enum('м','шт') NOT NULL DEFAULT 'м',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nomenclature_number` (`barcode`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;

-- Дамп данных таблицы sls_sklad_goods.products: ~1 rows (приблизительно)
INSERT INTO `products` (`id`, `barcode`, `product_name`, `product_width`, `product_units`, `created_at`, `updated_at`) VALUES
	(1, 2109800004039, 'YN-J-21039 C#nude/gold 9/21', 140, 'м', '2024-10-09 21:42:05', '2024-10-09 23:42:17'),
	(2, 2109800004053, 'YN-J-21039 C#4 grey 9/21', 140, 'м', '2024-10-10 00:53:16', '2024-10-10 00:53:16'),
	(3, 2109800009683, 'RBN0500 #6 Black (23/1)', 140, 'м', '2024-10-10 05:04:25', '2024-10-10 05:04:25');

-- Дамп структуры для таблица sls_sklad_goods.product_materials
CREATE TABLE IF NOT EXISTS `product_materials` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product_id` int(11) NOT NULL,
  `material_id` tinyint(3) NOT NULL,
  `proportion` decimal(5,2) NOT NULL COMMENT 'Процент материала в составе ткани',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `FK_productmaterials_materials` (`material_id`),
  KEY `FK_productmaterials_products` (`product_id`),
  CONSTRAINT `FK_productmaterials_materials` FOREIGN KEY (`material_id`) REFERENCES `materials` (`id`),
  CONSTRAINT `FK_productmaterials_products` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;

-- Дамп данных таблицы sls_sklad_goods.product_materials: ~2 rows (приблизительно)
INSERT INTO `product_materials` (`id`, `product_id`, `material_id`, `proportion`, `created_at`, `updated_at`) VALUES
	(1, 1, 2, 96.00, '2024-10-09 21:42:05', '2024-10-09 23:43:52'),
	(2, 1, 3, 4.00, '2024-10-09 21:42:05', '2024-10-09 23:43:56'),
	(3, 2, 2, 96.00, '2024-10-10 00:53:46', '2024-10-10 00:53:46'),
	(4, 2, 3, 4.00, '2024-10-10 00:54:00', '2024-10-10 00:54:00'),
	(5, 3, 1, 100.00, '2024-10-10 05:07:30', '2024-10-10 05:07:30');

-- Дамп структуры для таблица sls_sklad_goods.product_photos
CREATE TABLE IF NOT EXISTS `product_photos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product_id` int(11) NOT NULL,
  `photo_url` varchar(255) NOT NULL COMMENT 'Ссылка на фото товара',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `FK_product_photos_products` (`product_id`) USING BTREE,
  CONSTRAINT `FK_product_photos_products` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Дамп данных таблицы sls_sklad_goods.product_photos: ~0 rows (приблизительно)

-- Дамп структуры для таблица sls_sklad_goods.product_prices
CREATE TABLE IF NOT EXISTS `product_prices` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `stock_id` int(11) NOT NULL,
  `price` decimal(5,2) NOT NULL COMMENT 'Цена товара на складе',
  `currency_id` tinyint(1) NOT NULL DEFAULT '2',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `FK_product_prices_stock` (`stock_id`) USING BTREE,
  KEY `FK_product_prices_currencies` (`currency_id`),
  CONSTRAINT `FK_product_prices_currencies` FOREIGN KEY (`currency_id`) REFERENCES `currencies` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `FK_product_prices_stock` FOREIGN KEY (`stock_id`) REFERENCES `stock` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8;

-- Дамп данных таблицы sls_sklad_goods.product_prices: ~6 rows (приблизительно)
INSERT INTO `product_prices` (`id`, `stock_id`, `price`, `currency_id`, `created_at`, `updated_at`) VALUES
	(1, 1, 27.00, 1, '2024-10-10 01:13:10', '2024-10-10 01:13:10'),
	(2, 2, 27.00, 1, '2024-10-10 01:14:05', '2024-10-10 01:14:05'),
	(3, 3, 27.00, 1, '2024-10-10 01:14:14', '2024-10-10 01:14:14'),
	(4, 4, 27.00, 1, '2024-10-10 01:14:52', '2024-10-10 01:14:52'),
	(5, 5, 27.00, 1, '2024-10-10 01:15:08', '2024-10-10 01:15:08'),
	(6, 6, 27.00, 1, '2024-10-10 01:15:14', '2024-10-10 01:15:14'),
	(7, 7, 10.00, 1, '2024-10-10 05:20:42', '2024-10-10 05:20:42'),
	(8, 8, 10.00, 1, '2024-10-10 05:20:53', '2024-10-10 05:20:53'),
	(9, 9, 10.00, 1, '2024-10-10 05:21:02', '2024-10-10 05:21:02');

-- Дамп структуры для представление sls_sklad_goods.show_remaining_products
-- Создание временной таблицы для обработки ошибок зависимостей представлений
CREATE TABLE `show_remaining_products` (
	`barcode` BIGINT(13) NOT NULL,
	`product_name` VARCHAR(1) NOT NULL COLLATE 'utf8_general_ci',
	`short_name` VARCHAR(1) NOT NULL COLLATE 'utf8_general_ci',
	`warehouse_name` VARCHAR(1) NOT NULL COLLATE 'utf8_general_ci',
	`warehouse_number` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_general_ci',
	`total_quantity` DECIMAL(29,3) NULL,
	`shelves` VARCHAR(1) NULL COLLATE 'utf8_general_ci',
	`composition` VARCHAR(1) NULL COLLATE 'utf8_general_ci'
) ENGINE=MyISAM;

-- Дамп структуры для таблица sls_sklad_goods.stock
CREATE TABLE IF NOT EXISTS `stock` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product_id` int(11) NOT NULL,
  `warehouse_id` smallint(3) NOT NULL,
  `quantity` decimal(7,3) unsigned NOT NULL DEFAULT '0.000' COMMENT 'Количество на складе',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `FK_stock_warehouses` (`warehouse_id`),
  KEY `FK_stock_products` (`product_id`),
  CONSTRAINT `FK_stock_products` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `FK_stock_warehouses` FOREIGN KEY (`warehouse_id`) REFERENCES `warehouses` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8;

-- Дамп данных таблицы sls_sklad_goods.stock: ~7 rows (приблизительно)
INSERT INTO `stock` (`id`, `product_id`, `warehouse_id`, `quantity`, `created_at`, `updated_at`) VALUES
	(1, 1, 4, 21.620, '2024-10-09 23:52:58', '2024-10-10 05:13:36'),
	(2, 1, 2, 22.200, '2024-10-09 23:57:46', '2024-10-10 05:14:09'),
	(3, 1, 3, 9.090, '2024-10-10 00:04:04', '2024-10-10 05:14:25'),
	(4, 2, 4, 6.920, '2024-10-10 00:55:15', '2024-10-10 05:15:41'),
	(5, 2, 2, 13.300, '2024-10-10 00:56:02', '2024-10-10 05:15:22'),
	(6, 2, 3, 24.580, '2024-10-10 00:56:42', '2024-10-10 05:14:57'),
	(7, 3, 4, 1327.173, '2024-10-10 05:08:52', '2024-10-10 05:12:25'),
	(8, 3, 2, 178.873, '2024-10-10 05:16:56', '2024-10-10 05:16:56'),
	(9, 3, 3, 129.200, '2024-10-10 05:17:16', '2024-10-10 05:17:16');

-- Дамп структуры для таблица sls_sklad_goods.storage_locations
CREATE TABLE IF NOT EXISTS `storage_locations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `stock_id` int(11) NOT NULL,
  `location_description` varchar(255) NOT NULL COMMENT 'Описание места хранения товара',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `FK_storage_locations_stock` (`stock_id`) USING BTREE,
  CONSTRAINT `FK_storage_locations_stock` FOREIGN KEY (`stock_id`) REFERENCES `stock` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8 COMMENT='Место Хранения';

-- Дамп данных таблицы sls_sklad_goods.storage_locations: ~0 rows (приблизительно)
INSERT INTO `storage_locations` (`id`, `stock_id`, `location_description`, `created_at`, `updated_at`) VALUES
	(1, 1, 'Д-22', '2024-10-10 00:06:55', '2024-10-10 00:07:48'),
	(2, 1, ' XP', '2024-10-10 00:08:02', '2024-10-10 00:08:02'),
	(3, 2, 'D-6-2', '2024-10-10 00:08:32', '2024-10-10 00:08:32'),
	(4, 4, 'Д-18', '2024-10-10 00:57:25', '2024-10-10 00:57:25'),
	(5, 4, 'Д-17', '2024-10-10 00:57:48', '2024-10-10 00:57:48'),
	(6, 4, 'XP', '2024-10-10 00:58:00', '2024-10-10 00:58:00'),
	(7, 5, 'D-6-2', '2024-10-10 00:58:24', '2024-10-10 00:58:24'),
	(8, 7, 'Б-16', '2024-10-10 05:18:30', '2024-10-10 05:18:30'),
	(9, 7, 'XP', '2024-10-10 05:18:43', '2024-10-10 05:18:43'),
	(10, 8, 'J-5-5', '2024-10-10 05:19:02', '2024-10-10 05:19:02'),
	(11, 8, 'J-5-6', '2024-10-10 05:19:12', '2024-10-10 05:19:12'),
	(12, 8, 'ХР', '2024-10-10 05:19:21', '2024-10-10 05:19:21'),
	(13, 9, 'ХР', '2024-10-10 05:19:38', '2024-10-10 05:19:38');

-- Дамп структуры для таблица sls_sklad_goods.warehouses
CREATE TABLE IF NOT EXISTS `warehouses` (
  `id` smallint(3) NOT NULL AUTO_INCREMENT,
  `internal_number` smallint(3) unsigned zerofill NOT NULL DEFAULT '000',
  `warehouse_short_name` char(8) NOT NULL,
  `warehouse_name` varchar(100) NOT NULL,
  `currency_id` tinyint(1) NOT NULL DEFAULT '2',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `internal_number` (`internal_number`),
  KEY `FK_warehouses_currencies` (`currency_id`),
  CONSTRAINT `FK_warehouses_currencies` FOREIGN KEY (`currency_id`) REFERENCES `currencies` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

-- Дамп данных таблицы sls_sklad_goods.warehouses: ~4 rows (приблизительно)
INSERT INTO `warehouses` (`id`, `internal_number`, `warehouse_short_name`, `warehouse_name`, `currency_id`, `created_at`, `updated_at`) VALUES
	(1, 070, 'MSK-WH70', 'Склад хранения', 1, '2024-10-09 21:56:14', '2024-10-10 01:17:20'),
	(2, 071, 'MSK-LT', 'ЛегаТессиле (Варшавка)', 1, '2024-10-09 23:37:46', '2024-10-10 01:17:22'),
	(3, 035, 'MSK-IT', 'Кутюр', 1, '2024-10-09 23:38:29', '2024-10-10 01:17:23'),
	(4, 037, 'MSK-TL', 'Огород', 1, '2024-10-09 23:39:02', '2024-10-10 01:17:25');

-- Дамп структуры для представление sls_sklad_goods._show_remaining_products_0
-- Создание временной таблицы для обработки ошибок зависимостей представлений
CREATE TABLE `_show_remaining_products_0` (
	`barcode` BIGINT(13) NOT NULL,
	`product_name` VARCHAR(1) NOT NULL COLLATE 'utf8_general_ci',
	`short_name` CHAR(8) NOT NULL COLLATE 'utf8_general_ci',
	`warehouse_name` VARCHAR(1) NOT NULL COLLATE 'utf8_general_ci',
	`warehouse_number` SMALLINT(3) UNSIGNED ZEROFILL NOT NULL,
	`total_quantity` DECIMAL(29,3) NULL,
	`shelves` TEXT NULL COLLATE 'utf8_general_ci'
) ENGINE=MyISAM;

-- Дамп структуры для представление sls_sklad_goods._show_remaining_products_1
-- Создание временной таблицы для обработки ошибок зависимостей представлений
CREATE TABLE `_show_remaining_products_1` 
) ENGINE=MyISAM;

-- Удаление временной таблицы и создание окончательной структуры представления
DROP TABLE IF EXISTS `show_remaining_products`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `show_remaining_products` AS select `p`.`barcode` AS `barcode`,`p`.`product_name` AS `product_name`,coalesce(`w`.`warehouse_short_name`,'-') AS `short_name`,coalesce(`w`.`warehouse_name`,'-') AS `warehouse_name`,coalesce(`w`.`internal_number`,'-') AS `warehouse_number`,sum(`s`.`quantity`) AS `total_quantity`,coalesce((select group_concat(`sl`.`location_description` order by `sl`.`location_description` ASC separator ', ') from `storage_locations` `sl` where (`sl`.`stock_id` = `s`.`id`)),'') AS `shelves`,coalesce((select group_concat(distinct concat(`m`.`material_name`,' (',`pm`.`proportion`,'%)') order by `pm`.`proportion` DESC separator ', ') from (`product_materials` `pm` join `materials` `m` on((`pm`.`material_id` = `m`.`id`))) where (`pm`.`product_id` = `p`.`id`)),'') AS `composition` from ((`stock` `s` join `products` `p` on((`s`.`product_id` = `p`.`id`))) join `warehouses` `w` on((`s`.`warehouse_id` = `w`.`id`))) where (`p`.`barcode` = '2109800009683') group by `p`.`barcode`,`p`.`product_name`,`w`.`warehouse_short_name`,`w`.`warehouse_name`,`w`.`internal_number` having (`total_quantity` >= 5);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
