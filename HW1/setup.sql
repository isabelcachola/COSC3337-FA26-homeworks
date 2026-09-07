-- ---------------------------------------------------------------------
-- COSC 3337 — HW 1: create the read-only account used for Part 2.
--
-- Run once, after loading soundwave.sql and soundwave_small.sql:
--
--     sudo mysql < setup.sql
--
-- Why a separate account: every question in this assignment is a read.  An
-- account that can only SELECT cannot drop a table, empty one, or corrupt the
-- data no matter what you paste into it — which matters here, because there is
-- no backup image of your VM.  Keep using `sudo mysql` for administration and
-- `soundwave_ro` for the homework.
--
-- Change the password below if you like; if you do, use it when you connect.
-- ---------------------------------------------------------------------

CREATE USER IF NOT EXISTS 'soundwave_ro'@'localhost'
  IDENTIFIED BY 'soundwave';

GRANT SELECT ON soundwave.*       TO 'soundwave_ro'@'localhost';
GRANT SELECT ON soundwave_small.* TO 'soundwave_ro'@'localhost';

FLUSH PRIVILEGES;

-- Connect with:   mysql -u soundwave_ro -p soundwave
SELECT 'read-only account soundwave_ro is ready' AS status;
