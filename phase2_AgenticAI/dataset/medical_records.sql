CREATE DATABASE IF NOT EXISTS medical CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE medical;

drop table patients;

CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(10)     primary key, 
    gender ENUM('Male','Female') NOT NULL,
    age TINYINT         UNSIGNED NOT NULL,
    -- Vitals
    bp_s SMALLINT        UNSIGNED NOT NULL,
    bp_d SMALLINT        UNSIGNED NOT NULL,
    heart_rate SMALLINT        UNSIGNED NOT NULL,
    spo2 TINYINT UNSIGNED NOT NULL,
    resp_rate        TINYINT         UNSIGNED NOT NULL,       -- breaths/min
    weight               DECIMAL(5,1)    NOT NULL,
    height               DECIMAL(5,1)    NOT NULL,
    temp           DECIMAL(4,1)    NOT NULL,               -- °C

    -- Clinical
    present_complaint       VARCHAR(100)    NOT NULL,
    past_med_history    VARCHAR(255)    NOT NULL,               -- semicolon-separated
    allergies               VARCHAR(100)    NOT NULL,

    -- Surgical & Social
    past_surg_history   VARCHAR(255)    NOT NULL,               -- semicolon-separated
    social_hist          VARCHAR(300)    NOT NULL,               -- Alcohol; Tobacco; Drugs

    -- Audit
    created_at              TIMESTAMP       DEFAULT CURRENT_TIMESTAMP

);

select * from patients;
-- ============================================================
--  Useful indexes for querying
-- ============================================================

CREATE INDEX idx_gender       ON patients (gender);
CREATE INDEX idx_age          ON patients (age);
CREATE INDEX idx_complaint    ON patients (present_complaint);
CREATE INDEX idx_spo2         ON patients (spo2);
CREATE INDEX idx_heart_rate   ON patients (heart_rate);