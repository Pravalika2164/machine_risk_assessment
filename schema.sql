
-- Dynamic Machine Data Management & Local Risk Prediction
-- MySQL database schema

CREATE DATABASE IF NOT EXISTS machine_risks_db;

USE machine_risks_db;

-- Configurable field definitions
CREATE TABLE IF NOT EXISTS fields (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL,
    type ENUM('text', 'number', 'dropdown') NOT NULL,
    required BOOLEAN NOT NULL DEFAULT FALSE,
    options JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Machine records with dynamic JSON attributes
CREATE TABLE IF NOT EXISTS machines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);
