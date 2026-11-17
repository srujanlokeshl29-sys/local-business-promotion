-- =====================================================================
-- LOCAL BUSINESS PROMOTION AND MARKET ANALYTICS PORTAL (LocalBiz)
-- Database: localbiz
-- Target: MySQL 5.7+ / 8.0+ / MariaDB
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `localbiz` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `localbiz`;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(120) NOT NULL,
    `email` VARCHAR(150) NOT NULL UNIQUE,
    `phone` VARCHAR(20) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('customer', 'owner', 'admin') NOT NULL DEFAULT 'customer',
    `preferred_language` VARCHAR(10) NOT NULL DEFAULT 'en',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_users_email` (`email`),
    INDEX `idx_users_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. CATEGORIES TABLE
CREATE TABLE IF NOT EXISTS `categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(80) NOT NULL UNIQUE,
    `kannada_name` VARCHAR(120) NOT NULL,
    `icon` VARCHAR(20) NOT NULL DEFAULT '🏪',
    `description` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. BUSINESSES TABLE
CREATE TABLE IF NOT EXISTS `businesses` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `owner_id` INT NOT NULL,
    `category_id` INT NOT NULL,
    `business_name` VARCHAR(150) NOT NULL,
    `description` TEXT,
    `address` VARCHAR(255) NOT NULL,
    `city` VARCHAR(80) NOT NULL DEFAULT 'Hiriyur',
    `phone` VARCHAR(20) NOT NULL,
    `email` VARCHAR(150),
    `website` VARCHAR(200),
    `status` ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    `rating` DECIMAL(3, 2) NOT NULL DEFAULT 0.00,
    `total_reviews` INT NOT NULL DEFAULT 0,
    `view_count` INT NOT NULL DEFAULT 0,
    `image_url` VARCHAR(255) DEFAULT 'default_business.jpg',
    `latitude` DECIMAL(10, 7) DEFAULT 13.9450000,
    `longitude` DECIMAL(10, 7) DEFAULT 76.6210000,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`owner_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) ON DELETE RESTRICT,
    INDEX `idx_business_status` (`status`),
    INDEX `idx_business_city` (`city`),
    INDEX `idx_business_rating` (`rating`),
    INDEX `idx_business_category` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. PRODUCTS TABLE
CREATE TABLE IF NOT EXISTS `products` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `business_id` INT NOT NULL,
    `product_name` VARCHAR(150) NOT NULL,
    `description` TEXT,
    `price` DECIMAL(10, 2) NOT NULL,
    `unit` VARCHAR(50) DEFAULT 'piece',
    `image_url` VARCHAR(255) DEFAULT 'default_product.jpg',
    `is_available` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`business_id`) REFERENCES `businesses`(`id`) ON DELETE CASCADE,
    INDEX `idx_products_business` (`business_id`),
    INDEX `idx_products_name` (`product_name`),
    INDEX `idx_products_price` (`price`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. OFFERS TABLE
CREATE TABLE IF NOT EXISTS `offers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `business_id` INT NOT NULL,
    `title` VARCHAR(150) NOT NULL,
    `description` TEXT,
    `discount_percent` DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    `coupon_code` VARCHAR(50),
    `valid_until` DATE NOT NULL,
    `clicks_count` INT NOT NULL DEFAULT 0,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`business_id`) REFERENCES `businesses`(`id`) ON DELETE CASCADE,
    INDEX `idx_offers_business` (`business_id`),
    INDEX `idx_offers_active` (`is_active`, `valid_until`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. REVIEWS TABLE
CREATE TABLE IF NOT EXISTS `reviews` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `business_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `rating` INT NOT NULL CHECK (`rating` BETWEEN 1 AND 5),
    `comment` TEXT NOT NULL,
    `is_reported` BOOLEAN NOT NULL DEFAULT FALSE,
    `report_reason` VARCHAR(255),
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`business_id`) REFERENCES `businesses`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_reviews_business` (`business_id`),
    INDEX `idx_reviews_reported` (`is_reported`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. ENQUIRIES TABLE
CREATE TABLE IF NOT EXISTS `enquiries` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `business_id` INT NOT NULL,
    `user_id` INT,
    `customer_name` VARCHAR(120) NOT NULL,
    `customer_phone` VARCHAR(20) NOT NULL,
    `customer_email` VARCHAR(150),
    `message` TEXT NOT NULL,
    `status` ENUM('new', 'read', 'replied') NOT NULL DEFAULT 'new',
    `reply_message` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`business_id`) REFERENCES `businesses`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    INDEX `idx_enquiries_business` (`business_id`),
    INDEX `idx_enquiries_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. BUSINESS_VIEWS TABLE
CREATE TABLE IF NOT EXISTS `business_views` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `business_id` INT NOT NULL,
    `ip_address` VARCHAR(50),
    `user_id` INT,
    `viewed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`business_id`) REFERENCES `businesses`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    INDEX `idx_views_business` (`business_id`),
    INDEX `idx_views_date` (`viewed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. SEARCH_HISTORY TABLE
CREATE TABLE IF NOT EXISTS `search_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT,
    `search_query` VARCHAR(200),
    `category_filter` VARCHAR(100),
    `location_filter` VARCHAR(100),
    `searched_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    INDEX `idx_search_query` (`search_query`),
    INDEX `idx_search_date` (`searched_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- INITIAL SEED DATA
-- Default Passwords for testing:
-- admin@localbiz.com -> Admin@123
-- owner@localbiz.com -> Owner@123
-- customer@localbiz.com -> Customer@123
-- (Hashes generated using Werkzeug scrypt/pbkdf2)
-- =====================================================================

INSERT INTO `categories` (`id`, `name`, `kannada_name`, `icon`, `description`) VALUES
(1, 'Restaurants & Cafes', 'ರೆಸ್ಟೋರೆಂಟ್‌ಗಳು ಮತ್ತು ಕೆಫೆಗಳು', '🍔', 'Local eateries, traditional cuisine, cafes, and bakeries'),
(2, 'Mobile & Electronics', 'ಮೊಬೈಲ್ ಮತ್ತು ಎಲೆಕ್ಟ್ರಾನಿಕ್ಸ್', '📱', 'Smartphones, gadgets, repairs, and electronic accessories'),
(3, 'Clothing & Fashion', 'ಬಟ್ಟೆ ಮತ್ತು ಫ್ಯಾಷನ್', '👕', 'Ethnic wear, western clothes, boutiques, and footwear'),
(4, 'Grocery & Supermarket', 'ದಿನಸಿ ಮತ್ತು ಸೂಪರ್‌ಮಾರ್ಕೆಟ್', '🛒', 'Daily essentials, fresh vegetables, pulses, and spices'),
(5, 'Salons & Personal Care', 'ಸಲೂನ್‌ಗಳು ಮತ್ತು ಸೌಂದರ್ಯ', '💇', 'Hair dressing, spa, grooming, and skincare centers'),
(6, 'Health & Pharmacy', 'ಆರೋಗ್ಯ ಮತ್ತು ಔಷಧಾಲಯ', '💊', 'Clinics, pharmacies, medical supplies, and ayurveda'),
(7, 'Books & Education', 'ಪುಸ್ತಕಗಳು ಮತ್ತು ಶಿಕ್ಷಣ', '📚', 'School & college books, stationery, printing, and study supplies'),
(8, 'Auto & Transport', 'ವಾಹನ ಮತ್ತು ಸಾರಿಗೆ', '🚗', 'Bike & car repairs, engine oil, spare parts, and tyre care'),
(9, 'Electricals & Hardware', 'ಎಲೆಕ್ಟ್ರಿಕಲ್ ಮತ್ತು ಹಾರ್ಡ್‌ವೇರ್', '⚡', 'Fans, LED lights, plumbing fixtures, cables, and tools'),
(10, 'Jewelry & Watches', 'ಚಿನ್ನ, ಬೆಳ್ಳಿ ಮತ್ತು ಕೈಗಡಿಯಾರಗಳು', '💎', 'Traditional silver articles, gift items, watches, and ornaments')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);
