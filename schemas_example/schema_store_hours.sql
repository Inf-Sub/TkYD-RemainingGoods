CREATE TABLE IF NOT EXISTS store_hours (
    id TINYINT(2) NOT NULL AUTO_INCREMENT,
    store_id CHAR(6) NOT NULL,
    # week_days SET('Mon','Tue','Wed','Thu','Fri','Sat','Sun') NOT NULL DEFAULT 'Mon,Tue,Wed,Thu,Fri,Sat,Sun',
    week_days ENUM('weekdays','weekends') NOT NULL DEFAULT 'weekdays',
    opening_time TIME NULL DEFAULT '09:00:00',
    closing_time TIME NULL DEFAULT '19:00:00',
    PRIMARY KEY (id),
    INDEX FK_store_hours_stores (store_id),
    CONSTRAINT FK_store_hours_stores FOREIGN KEY (store_id) REFERENCES stores (identity) ON UPDATE CASCADE ON DELETE RESTRICT
) COMMENT='Часы работы магазинов';
