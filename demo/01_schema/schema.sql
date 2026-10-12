-- Step 1: schema.  Run:  mysql < 01_schema/schema.sql
-- Re-running drops and recreates everything, so the demo is repeatable.

DROP DATABASE IF EXISTS club_events;
CREATE DATABASE club_events CHARACTER SET utf8mb4;
USE club_events;

CREATE TABLE clubs (
  club_id      INT AUTO_INCREMENT PRIMARY KEY,
  name         VARCHAR(80)  NOT NULL UNIQUE,
  description  VARCHAR(255)
);

CREATE TABLE members (
  member_id  INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(80)  NOT NULL,
  email      VARCHAR(120) NOT NULL UNIQUE
);

-- One club hosts many events (1-to-many).
CREATE TABLE events (
  event_id    INT AUTO_INCREMENT PRIMARY KEY,
  club_id     INT          NOT NULL,
  title       VARCHAR(120) NOT NULL,
  location    VARCHAR(80)  NOT NULL,
  start_time  DATETIME     NOT NULL,
  end_time    DATETIME     NOT NULL,
  FOREIGN KEY (club_id) REFERENCES clubs (club_id) ON DELETE CASCADE,
  CHECK (end_time > start_time)
);

-- Members and events are many-to-many; rsvps is the junction table.
-- The composite primary key means one RSVP per (member, event): a second
-- attempt is rejected by the database, no matter what the app does.
CREATE TABLE rsvps (
  member_id  INT NOT NULL,
  event_id   INT NOT NULL,
  status     ENUM('going', 'maybe', 'not_going') NOT NULL DEFAULT 'going',
  rsvp_time  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (member_id, event_id),
  FOREIGN KEY (member_id) REFERENCES members (member_id) ON DELETE CASCADE,
  FOREIGN KEY (event_id)  REFERENCES events  (event_id)  ON DELETE CASCADE
);
