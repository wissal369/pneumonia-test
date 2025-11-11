create database xray_db ;
use xray_db ;
 CREATE TABLE IF NOT EXISTS predictions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                image_path VARCHAR(255),
                result VARCHAR(50),
                confidence FLOAT,
                date DATETIME
            );