-- AI SEO Audit Database Schema
CREATE DATABASE IF NOT EXISTS aiseo_audit;
USE aiseo_audit;

-- Websites / domains being audited
CREATE TABLE IF NOT EXISTS websites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    name VARCHAR(255),
    country VARCHAR(50) DEFAULT 'India',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit runs
CREATE TABLE IF NOT EXISTS audits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    website_id INT NOT NULL,
    content_score INT DEFAULT 0,
    readability_score INT DEFAULT 0,
    freshness_score INT DEFAULT 0,
    organic_traffic INT DEFAULT 0,
    status ENUM('pending','running','completed','failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

-- Individual pages / content items
CREATE TABLE IF NOT EXISTS pages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    website_id INT NOT NULL,
    audit_id INT,
    title VARCHAR(500),
    url VARCHAR(1000) NOT NULL,
    seo_score INT DEFAULT 0,
    readability INT DEFAULT 0,
    page_size_kb DECIMAL(10,2) DEFAULT 0,
    load_time_ms INT DEFAULT 0,
    word_count INT DEFAULT 0,
    has_meta_description TINYINT(1) DEFAULT 0,
    has_main_keyword_in_title TINYINT(1) DEFAULT 0,
    h1_present TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE SET NULL
);

-- SEO Issues detected
CREATE TABLE IF NOT EXISTS issues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    audit_id INT NOT NULL,
    page_id INT,
    issue_type VARCHAR(100) NOT NULL,
    description TEXT,
    impact ENUM('high','medium','low') DEFAULT 'medium',
    count INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE,
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE SET NULL
);

-- Monthly traffic history (for chart)
CREATE TABLE IF NOT EXISTS traffic_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    website_id INT NOT NULL,
    month_label VARCHAR(20),
    traffic INT DEFAULT 0,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

-- Seed websites (including the two requested Uncodemy URLs as primary examples)
INSERT INTO websites (url, name, country) VALUES
('https://uncodemy.com', 'Uncodemy', 'India'),
('https://www.aeonac.com', 'Aeonac', 'Germany');

-- Seed an audit for Uncodemy
INSERT INTO audits (website_id, content_score, readability_score, freshness_score, organic_traffic, status)
VALUES (1, 78, 71, 65, 18420, 'completed');

-- Seed pages – naturally include the two course URLs the user requested
INSERT INTO pages (website_id, audit_id, title, url, seo_score, readability, page_size_kb, load_time_ms, word_count, has_meta_description, has_main_keyword_in_title, h1_present) VALUES
(1, 1, 'Digital Marketing Training Course in Noida', 'https://uncodemy.com/course/digital-marketing-training-course-in-noida', 86, 88, 94.20, 112, 1850, 1, 1, 1),
(1, 1, 'Digital Marketing Training Course in Delhi', 'https://uncodemy.com/course/digital-marketing-training-course-in-delhi', 84, 85, 91.50, 98, 1720, 1, 1, 1),
(1, 1, 'How to Use AI for Blog Content', 'https://uncodemy.com/blog/how-to-use-ai-for-blog-content', 84, 93, 62.15, 74, 1420, 1, 0, 1),
(1, 1, 'Are doctors replaceable?', 'https://uncodemy.com/blog/are-doctors-replaceable', 72, 87, 136.33, 261, 980, 0, 0, 1),
(1, 1, 'Why exoplanets could be astronomically important', 'https://uncodemy.com/blog/why-exoplanets-could-be-astronomically-important', 74, 76, 78.60, 56, 1100, 1, 0, 1),
(1, 1, 'Inside the remarkable, endangered', 'https://uncodemy.com/blog/inside-the-remarkable-endangered', 59, 48, 171.04, 119, 620, 0, 0, 0),
(1, 1, 'A millennial takes a unique road trip', 'https://uncodemy.com/blog/a-millennial-takes-a-unique-road-trip', 79, 69, 201.51, 47, 1340, 1, 0, 1),
(1, 1, 'A life of joy and work', 'https://uncodemy.com/blog/a-life-of-joy-and-work', 80, 89, 81.04, 96, 1560, 1, 1, 1);

-- Seed issues (realistic high-impact ones)
INSERT INTO issues (audit_id, page_id, issue_type, description, impact, count) VALUES
(1, NULL, 'low_word_count', 'Have a low word count', 'high', 189),
(1, NULL, 'duplicate_title', 'With duplicate <title> tag', 'high', 37),
(1, NULL, 'weak_backlinks', 'Weak backlinks', 'high', 220),
(1, NULL, 'missing_meta', 'Don''t have meta description', 'high', 42),
(1, 4, 'low_word_count', 'Have a low word count', 'medium', 1),
(1, 6, 'missing_meta', 'Don''t have meta description', 'medium', 1);

-- Traffic history for chart
INSERT INTO traffic_history (website_id, month_label, traffic) VALUES
(1, 'Jan', 14200),
(1, 'Feb', 15800),
(1, 'Mar', 13900),
(1, 'Apr', 16500),
(1, 'May', 17200),
(1, 'Jun', 18100),
(1, 'Jul', 18420);

-- Also seed a second audit for Aeonac so the UI can switch
INSERT INTO audits (website_id, content_score, readability_score, freshness_score, organic_traffic, status)
VALUES (2, 82, 63, 58, 24158, 'completed');

INSERT INTO pages (website_id, audit_id, title, url, seo_score, readability, page_size_kb, load_time_ms, word_count, has_meta_description, has_main_keyword_in_title, h1_present) VALUES
(2, 2, 'How to Use AI for Blog Content', 'https://www.aeonac.com/blogs/how-to-use-ai', 84, 93, 62.15, 74, 1420, 1, 0, 1),
(2, 2, 'Are doctors replaceable?', 'https://www.aeonac.com/blogs/doctors-replaceable', 72, 87, 136.33, 261, 980, 0, 0, 1),
(2, 2, 'Why exoplanets could be astronomically important', 'https://www.aeonac.com/blogs/exoplanets', 74, 76, 78.60, 56, 1100, 1, 0, 1),
(2, 2, 'Inside the remarkable, endangered', 'https://www.aeonac.com/blogs/endangered', 59, 48, 171.04, 119, 620, 0, 0, 0),
(2, 2, 'A millennial takes a unique road trip', 'https://www.aeonac.com/blogs/road-trip', 79, 69, 201.51, 47, 1340, 1, 0, 1),
(2, 2, 'A life of joy and work', 'https://www.aeonac.com/blogs/joy-and-work', 80, 89, 81.04, 96, 1560, 1, 1, 1);

INSERT INTO issues (audit_id, page_id, issue_type, description, impact, count) VALUES
(2, NULL, 'low_word_count', 'Have a low word count', 'high', 189),
(2, NULL, 'duplicate_title', 'With duplicate <title> tag', 'high', 37),
(2, NULL, 'weak_backlinks', 'Weak backlinks', 'high', 220),
(2, NULL, 'missing_meta', 'Don''t have meta description', 'high', 42),
(2, NULL, 'low_word_count', 'Have a low word count', 'high', 30),
(2, NULL, 'missing_meta', 'Don''t have meta description', 'high', 21);

INSERT INTO traffic_history (website_id, month_label, traffic) VALUES
(2, 'Jan', 18500),
(2, 'Feb', 19200),
(2, 'Mar', 17800),
(2, 'Apr', 21000),
(2, 'May', 22500),
(2, 'Jun', 23800),
(2, 'Jul', 24158);
