-- CivicConnect prototype MySQL schema

CREATE TABLE IF NOT EXISTS wards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ward_number INT NOT NULL,
    ward_code VARCHAR(50) NOT NULL,
    UNIQUE KEY uq_wards_number (ward_number),
    UNIQUE KEY uq_wards_code (ward_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'citizen',
    ward_id INT NOT NULL,
    CONSTRAINT fk_users_ward
        FOREIGN KEY (ward_id) REFERENCES wards (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ward_id INT NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    file_path VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'Submitted',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_complaints_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_complaints_ward
        FOREIGN KEY (ward_id) REFERENCES wards (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ward_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    contractor_name VARCHAR(150),
    budget DECIMAL(12,2),
    start_date DATE,
    deadline DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'Planned',
    progress_percentage INT NOT NULL DEFAULT 0,
    image_path VARCHAR(255),
    CONSTRAINT fk_projects_ward
        FOREIGN KEY (ward_id) REFERENCES wards (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ward_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(50) NOT NULL DEFAULT 'Normal',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_announcements_ward
        FOREIGN KEY (ward_id) REFERENCES wards (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- Sample seed data: one ward and one ward admin

INSERT INTO wards (ward_number, ward_code)
VALUES (1, 'WARD1')
ON DUPLICATE KEY UPDATE ward_number = VALUES(ward_number), ward_code = VALUES(ward_code);

-- NOTE: replace CHANGE_ME_HASH with a real hashed password or
-- use the create_sample_data() helper in models.py
INSERT INTO users (name, email, password_hash, role, ward_id)
VALUES ('Ward Admin', 'admin@civicconnect.local', 'CHANGE_ME_HASH', 'ward_admin', 1)
ON DUPLICATE KEY UPDATE email = VALUES(email);

