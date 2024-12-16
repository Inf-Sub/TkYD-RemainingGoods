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

-- Дамп структуры для таблица sls_sklad_goods.storage_locations
CREATE TABLE IF NOT EXISTS `storage_locations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `stock_id` int(11) NOT NULL,
  `location_name_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `FK_storage_locations_stock` (`stock_id`) USING BTREE,
  KEY `FK_storage_locations_storage_location_names` (`location_name_id`),
  CONSTRAINT `FK_storage_locations_stock` FOREIGN KEY (`stock_id`) REFERENCES `stock` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_storage_locations_storage_location_names` FOREIGN KEY (`location_name_id`) REFERENCES `storage_location_names` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8 COMMENT='Место Хранения';

-- Дамп данных таблицы sls_sklad_goods.storage_locations: ~13 rows (приблизительно)
REPLACE INTO `storage_locations` (`id`, `stock_id`, `location_name_id`, `created_at`, `updated_at`) VALUES
	(1, 1, 2, '2024-10-10 00:06:55', '2024-10-16 00:15:08'),
	(2, 1, 1, '2024-10-10 00:08:02', '2024-10-16 00:14:31'),
	(3, 2, 3, '2024-10-10 00:08:32', '2024-10-16 00:15:53'),
	(4, 4, 4, '2024-10-10 00:57:25', '2024-10-16 00:16:03'),
	(5, 4, 5, '2024-10-10 00:57:48', '2024-10-16 00:16:09'),
	(6, 4, 1, '2024-10-10 00:58:00', '2024-10-16 00:14:42'),
	(7, 5, 3, '2024-10-10 00:58:24', '2024-10-16 00:16:18'),
	(8, 7, 6, '2024-10-10 05:18:30', '2024-10-16 00:16:30'),
	(9, 7, 1, '2024-10-10 05:18:43', '2024-10-16 00:14:45'),
	(10, 8, 7, '2024-10-10 05:19:02', '2024-10-16 00:16:37'),
	(11, 8, 8, '2024-10-10 05:19:12', '2024-10-16 00:16:39'),
	(12, 8, 1, '2024-10-10 05:19:21', '2024-10-16 00:14:55'),
	(13, 9, 1, '2024-10-10 05:19:38', '2024-10-16 00:14:57');

-- Дамп структуры для таблица sls_sklad_goods.storage_location_comments
CREATE TABLE IF NOT EXISTS `storage_location_comments` (
  `location_id` int(11) NOT NULL,
  `description_id` mediumint(9) NOT NULL,
  PRIMARY KEY (`location_id`,`description_id`),
  KEY `FK_storage_location_comments_storage_location_descriptions` (`description_id`),
  CONSTRAINT `FK_storage_location_comments_storage_location_descriptions` FOREIGN KEY (`description_id`) REFERENCES `storage_location_descriptions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_storage_location_comments_storage_location_names` FOREIGN KEY (`location_id`) REFERENCES `storage_location_names` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Дамп данных таблицы sls_sklad_goods.storage_location_comments: ~1 rows (приблизительно)
REPLACE INTO `storage_location_comments` (`location_id`, `description_id`) VALUES
	(1, 1);

-- Дамп структуры для таблица sls_sklad_goods.storage_location_descriptions
CREATE TABLE IF NOT EXISTS `storage_location_descriptions` (
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `location_description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `location_description` (`location_description`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

-- Дамп данных таблицы sls_sklad_goods.storage_location_descriptions: ~1 rows (приблизительно)
REPLACE INTO `storage_location_descriptions` (`id`, `location_description`) VALUES
	(1, 'Хангеры');

-- Дамп структуры для таблица sls_sklad_goods.storage_location_names
CREATE TABLE IF NOT EXISTS `storage_location_names` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(10) NOT NULL COMMENT 'Уникальное наименование места хранения',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_location_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8 COMMENT='Уникальные Наименования Мест Хранения';

-- Дамп данных таблицы sls_sklad_goods.storage_location_names: ~8 rows (приблизительно)
REPLACE INTO `storage_location_names` (`id`, `name`) VALUES
	(3, 'D-6-2'),
	(7, 'J-5-5'),
	(8, 'J-5-6'),
	(1, 'XP'),
	(6, 'Б-16'),
	(5, 'Д-17'),
	(4, 'Д-18'),
	(2, 'Д-22');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
