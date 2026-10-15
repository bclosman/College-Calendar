const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

// Exercise date logic without a browser, network, or changes to real calendar data.
const source = fs.readFileSync(path.join(__dirname, "../frontend/app.js"), "utf8");
const setup = source.slice(0, source.indexOf('  $("previous").addEventListener'));
const context = { Intl, Date, document: {} };
vm.createContext(context);
vm.runInContext(setup + "globalThis.test = { state, configureDates, dateKey, sortKey, eventsOn, safeLink, calendarLayout }; })();", context);
const { state, configureDates, dateKey, sortKey, eventsOn, safeLink, calendarLayout } = context.test;
state.timezone = "America/Chicago";
configureDates();

assert.equal(dateKey("2026-10-15"), "2026-10-15");
assert.equal(dateKey("2026-10-15T02:00:00Z"), "2026-10-14");
assert.equal(sortKey("2026-10-15"), "2026-10-15T23:59:59");
assert.equal(dateKey("2026-10-15 09:00:00-05:00"), "2026-10-15");
assert.equal(dateKey("not a date"), null);

state.events = [{ calendar: "Classes", name: "All day", start: "2026-10-15", end: "2026-10-17" }];
assert.equal(eventsOn("2026-10-15").length, 1);
assert.equal(eventsOn("2026-10-16").length, 1);
assert.equal(eventsOn("2026-10-17").length, 0);

state.events = [{ calendar: "Classes", name: "Late event", start: "2026-10-15T23:00:00-05:00", end: "2026-10-16T00:00:00-05:00" }];
assert.equal(eventsOn("2026-10-15").length, 1);
assert.equal(eventsOn("2026-10-16").length, 0);
state.hidden.add("Classes");
assert.equal(eventsOn("2026-10-15").length, 0);

// The DST transition has two local 1:30 AM instants; both belong to November 1.
assert.equal(dateKey("2026-11-01T01:30:00-05:00"), "2026-11-01");
assert.equal(dateKey("2026-11-01T01:30:00-06:00"), "2026-11-01");
context.URL = URL;
assert.equal(safeLink("javascript:alert(1)"), null);
assert.equal(safeLink("https://example.com/assignment"), "https://example.com/assignment");
console.log("Frontend date, midnight, DST, calendar filter, and safe-link checks passed.");

assert.equal(calendarLayout(2026, 9, "2026-10-15", null).rows, 5);
assert.equal(calendarLayout(2026, 9, "2026-10-15", null).focusWeek, 2);
assert.equal(calendarLayout(2026, 9, "2026-10-15", "2026-10-21").focusWeek, 3);
assert.equal(calendarLayout(2026, 7, "2026-10-15", null).rows, 6);
assert.equal(calendarLayout(2026, 1, "2026-10-15", null).rows, 4);
assert.equal(calendarLayout(2026, 10, "2026-10-15", null).focusWeek, -1);
console.log("Four-, five-, and six-week months and focused-week selection passed.");
