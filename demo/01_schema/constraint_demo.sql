-- Step 1 "what if...": paste these into the mysql shell one at a time,
-- AFTER seeding (step 2). Each statement is supposed to FAIL.
USE club_events;

-- 1. Foreign key: club 999 does not exist.
INSERT INTO events (club_id, title, location, start_time, end_time)
VALUES (999, 'Ghost Event', 'Nowhere', '2030-01-01 18:00', '2030-01-01 19:00');

-- 2. CHECK: the event ends before it starts.
INSERT INTO events (club_id, title, location, start_time, end_time)
VALUES (1, 'Time Travel Mixer', 'Room 101', '2030-01-01 19:00', '2030-01-01 18:00');

-- 3. Primary key: member 1 already RSVPed to event 1 (seed guarantees this).
INSERT INTO rsvps (member_id, event_id) VALUES (1, 1);

-- 4. ENUM: 'definitely' is not an allowed status.
INSERT INTO rsvps (member_id, event_id, status) VALUES (4, 1, 'definitely');
