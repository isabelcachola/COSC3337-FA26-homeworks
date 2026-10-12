// Step 5: the front end only talks to the JSON API; it never sees SQL.
const memberSel = document.getElementById("member");
const clubSel = document.getElementById("club");
const eventsEl = document.getElementById("events");
const messageEl = document.getElementById("message");

async function api(path, options) {
  const res = await fetch(path, options);
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "Request failed");
  return body;
}

function say(text, isError = false) {
  messageEl.textContent = text;
  messageEl.className = isError ? "error" : "ok";
}

function fillSelect(select, rows, idKey) {
  for (const row of rows) {
    const opt = document.createElement("option");
    opt.value = row[idKey];
    opt.textContent = row.name;
    select.appendChild(opt);
  }
}

async function loadEvents() {
  const club = clubSel.value;
  const events = await api("/api/events" + (club ? `?club=${club}` : ""));
  eventsEl.replaceChildren();
  if (events.length === 0) eventsEl.textContent = "No upcoming events.";
  for (const ev of events) {
    const card = document.createElement("article");
    // textContent (not innerHTML) so database text can never inject markup.
    const when = new Date(ev.start_time).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
    card.innerHTML = "<h2></h2><p class='meta'></p><p class='count'></p>";
    card.querySelector("h2").textContent = ev.title;
    card.querySelector(".meta").textContent = `${ev.club_name} · ${ev.location} · ${when}`;
    card.querySelector(".count").textContent = `${ev.going_count} going`;
    const btn = document.createElement("button");
    btn.textContent = "RSVP";
    btn.addEventListener("click", () => rsvp(ev.event_id, ev.title));
    card.appendChild(btn);
    eventsEl.appendChild(card);
  }
}

async function rsvp(eventId, title) {
  try {
    await api("/api/rsvp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ member_id: Number(memberSel.value), event_id: eventId }),
    });
    say(`You're going to "${title}"!`);
    await loadEvents(); // re-query so the count comes from the database
  } catch (err) {
    say(err.message, true); // e.g. "already RSVPed to this event" from the 409
  }
}

async function init() {
  try {
    fillSelect(memberSel, await api("/api/members"), "member_id");
    fillSelect(clubSel, await api("/api/clubs"), "club_id");
    clubSel.addEventListener("change", () => { say(""); loadEvents(); });
    await loadEvents();
  } catch (err) {
    say(err.message, true);
  }
}
init();
