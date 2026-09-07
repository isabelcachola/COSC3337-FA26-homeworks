-- ---------------------------------------------------------------------
-- Soundwave — SMALL instance for COSC 3337 HW 1
--
-- These are exactly the seven artists, nine albums and sixteen tracks
-- printed in the handout.  Part 1 (relational algebra) is worked out by hand
-- against these tables; the translation questions in Part 2 run against this
-- database so that a correct SQL translation reproduces, row for row, the
-- tuples you computed on paper.
--
-- Hand-authored, NOT generated: if you change a value here you must change
-- the handout too.  The large `soundwave` database is generated separately
-- by generate_soundwave.py.
--
-- This script is idempotent.  Run it again at any time to restore a clean,
-- known-good database:
--
--     mysql -u root < soundwave_small.sql
-- ---------------------------------------------------------------------

DROP DATABASE IF EXISTS soundwave_small;
CREATE DATABASE soundwave_small CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE soundwave_small;

-- Same schema as the large database, so a query written against one runs
-- unchanged against the other.

CREATE TABLE artist (
  artist_id    VARCHAR(8)   NOT NULL,
  name         VARCHAR(80)  NOT NULL,
  country      VARCHAR(40)      NULL,
  formed_year  SMALLINT         NULL,
  PRIMARY KEY (artist_id)
) ENGINE=InnoDB;

CREATE TABLE album (
  album_id     VARCHAR(8)   NOT NULL,
  title        VARCHAR(120) NOT NULL,
  artist_id    VARCHAR(8)   NOT NULL,
  release_year SMALLINT         NULL,
  genre        VARCHAR(30)  NOT NULL,
  PRIMARY KEY (album_id),
  CONSTRAINT fk_small_album_artist
    FOREIGN KEY (artist_id) REFERENCES artist (artist_id)
) ENGINE=InnoDB;

CREATE TABLE track (
  track_id     VARCHAR(8)   NOT NULL,
  album_id     VARCHAR(8)   NOT NULL,
  title        VARCHAR(120) NOT NULL,
  duration_sec INT          NOT NULL,
  PRIMARY KEY (track_id),
  CONSTRAINT fk_small_track_album
    FOREIGN KEY (album_id) REFERENCES album (album_id)
) ENGINE=InnoDB;

INSERT INTO artist (artist_id, name, country, formed_year) VALUES
  ('A1', 'Neon Vale',        'USA',   2011),
  ('A2', 'Sofia Marchetti',  'Italy', 2004),
  ('A3', 'The Tidal',        'UK',    2016),
  ('A4', 'Kwame Osei',       'UK',    2013),
  ('A5', 'Hollow Pines',     'USA',   2009),
  ('A6', 'Yuki Tanabe',      'Japan', 2018),
  ('A7', 'Marta Reyes',      'Spain', 2015);

INSERT INTO album (album_id, title, artist_id, release_year, genre) VALUES
  ('B1', 'Glass Harbor',    'A1', 2019, 'Indie'),
  ('B2', 'Second Light',    'A1', 2022, 'Indie'),
  ('B3', 'Notturno',        'A2', 2018, 'Classical'),
  ('B4', 'Tide and Timber', 'A3', 2021, 'Rock'),
  ('B5', 'Accra Nights',    'A4', 2020, 'Afrobeat'),
  ('B6', 'Dust Chorus',     'A5', 2017, 'Folk'),
  ('B7', 'Dust Chorus II',  'A5', 2022, 'Folk'),
  ('B8', 'Kirameki',        'A6', 2023, 'Electronic'),
  ('B9', 'Cielo Bajo',      'A7', 2021, 'Latin');

INSERT INTO track (track_id, album_id, title, duration_sec) VALUES
  ('T01', 'B1', 'Harbor Lights', 245),
  ('T02', 'B1', 'Saltwater',     198),
  ('T03', 'B1', 'Glass',         312),
  ('T04', 'B2', 'Second Light',  224),
  ('T05', 'B2', 'Undertow',      187),
  ('T06', 'B3', 'Notturno I',    402),
  ('T07', 'B3', 'Notturno II',   355),
  ('T08', 'B4', 'Timber',        231),
  ('T09', 'B4', 'Spring Tide',   265),
  ('T10', 'B5', 'Accra Nights',  208),
  ('T11', 'B5', 'Highlife',      243),
  ('T12', 'B6', 'Dust',          279),
  ('T13', 'B7', 'Chorus',        196),
  ('T14', 'B8', 'Kirameki',      182),
  ('T15', 'B9', 'Cielo',         254),
  ('T16', 'B9', 'Bajo',          219);

-- ---------------------------------------------------------------------
-- Loaded: 7 artists, 9 albums, 16 tracks.
-- ---------------------------------------------------------------------
