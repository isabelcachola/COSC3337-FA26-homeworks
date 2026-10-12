-- Step 3: the queries the app needs. Try each one in the mysql shell BEFORE
-- putting it in Python. The @variables below stand in for values the app will
-- supply as parameters (the %s placeholders in Python).
USE club_events;
SET @club = NULL;          -- NULL = all clubs; try 2 for Robotics Society
SET @event_id = 1;
SET @member_id = 4;
SET @status = 'going';

-- Q1. Upcoming events, with club name and how many people are going.
--     Feeds GET /api/events. LEFT JOIN keeps events with zero RSVPs.
--     Optional club filter: pass NULL for "all clubs".
SELECT e.event_id, e.title, e.location, e.start_time,
       c.club_id, c.name AS club_name,
       COUNT(r.member_id) AS going_count
FROM events e
JOIN clubs c       ON c.club_id = e.club_id
LEFT JOIN rsvps r  ON r.event_id = e.event_id AND r.status = 'going'
WHERE e.start_time >= NOW()
  AND (@club IS NULL OR c.club_id = @club)
GROUP BY e.event_id, e.title, e.location, e.start_time, c.club_id, c.name
ORDER BY e.start_time;

-- Q2. Who is attending one event? Feeds GET /api/events/<id>.
SELECT m.member_id, m.name, r.status
FROM rsvps r
JOIN members m ON m.member_id = r.member_id
WHERE r.event_id = @event_id
ORDER BY r.rsvp_time;

-- Q3. Everything one member has RSVPed to (a many-to-many lookup).
SELECT e.title, c.name AS club_name, e.start_time, r.status
FROM rsvps r
JOIN events e ON e.event_id = r.event_id
JOIN clubs c  ON c.club_id = e.club_id
WHERE r.member_id = @member_id
ORDER BY e.start_time;

-- Q4. Create an RSVP. Feeds POST /api/rsvp. A duplicate fails with error 1062
--     (run it twice to see it). Member 4 has no RSVP yet, so the first run works.
INSERT INTO rsvps (member_id, event_id, status) VALUES (@member_id, @event_id, @status);

-- Q5. Clubs, for the front end's filter dropdown.
SELECT club_id, name FROM clubs ORDER BY name;
