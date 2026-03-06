## Student Name: Umer Shaikh
## Student ID: 218 931 790

"""
Task A: Appointment Timeslot Recommender (Stub)

In this lab, you will design and implement an Appointment Slot Recommender using an LLM assistant
as your primary programming collaborator.

You are asked to implement a Python module that recommends available meeting slots within a
defined working window.

The system must:
  • Accept working hours (start and end time).
  • Accept a list of existing busy intervals.
  • Accept a required meeting duration.
  • Accept an optional buffer time between meetings.
  • Optionally restrict suggestions to a candidate time window.
  • Return chronologically ordered appointment slots that satisfy all constraints.

The system must ensure that:
  • Suggested slots fall within working hours.
  • Suggested slots do not overlap busy intervals.
  • Buffer time is respected when evaluating availability.
  • Output ordering is deterministic under identical inputs.

The module must preserve the following invariants:
  • Returned slots must be at least as long as the required duration.
  • No returned slot may violate buffer constraints.
  • The returned list must reflect the current system state.

The system must correctly handle non-trivial scenarios such as:
  • Adjacent busy intervals.
  • Very small gaps between meetings.
  • Buffers eliminating otherwise valid availability.
  • Overlapping or unsorted busy intervals.
  • A meeting duration longer than any available gap.
  • No availability within the working window.

Output:
  The output consists of the next N valid appointment suggestions in chronological order.
  Behavior must be deterministic under ties (if any).

See the lab handout for full requirements.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional, Tuple


# ---------------- Data Models ----------------

@dataclass(frozen=True)
class TimeWindow:
    """
    A daily time window.
    Assumption (unless stated otherwise in handout): non-wrapping window where start < end.
    """

    start: time
    end: time


@dataclass(frozen=True)
class BusyInterval:
    """
    A busy interval on the given day.
    Invariant: start < end
    """

    start: time
    end: time


@dataclass(frozen=True)
class Slot:
    """
    A recommended appointment slot.

    start_time is a time-of-day within the working window.
    Deterministic ordering: sort by start_time ascending.
    """

    start_time: time


class InfeasibleSchedule(Exception):
    """Raised when no valid slots can be produced (if required by handout)."""

    pass


# ---------------- Core Function ----------------

def suggest_slots(
    day: date,
    working_hours: TimeWindow,
    busy_intervals: List[BusyInterval],
    duration: timedelta,
    n: int,
    buffer: timedelta = timedelta(0),
    candidate_window: Optional[TimeWindow] = None
) -> List[Slot]:
    """
    Suggest up to the next n valid appointment slots (start times) for the given day.

    Args:
        day: the calendar day for which to suggest slots.
        working_hours: the allowed working window for meetings (start < end).
        busy_intervals: list of busy time intervals (may be overlapping / unsorted).
        duration: required meeting length (must be > 0).
        n: maximum number of slot suggestions to return (n >= 0).
        buffer: optional buffer time required between meetings (buffer >= 0).
        candidate_window: optional extra restriction on suggestions (must lie within this window too).

    Returns:
        A list of Slot objects, sorted by start_time ascending, deterministic under identical inputs.
        If no suitable time slots are available, return an empty list.

    Notes:
        - Suggested slots must fall within working_hours (and candidate_window if provided).
        - Suggested slots must not overlap busy_intervals, considering buffer time.
        - You are free to choose internal representation; inputs use time-of-day.
        - See lab handout for required slot granularity (e.g., 5-min/15-min steps), if any.

    Implementation note:
        This function is implemented as an adapter around `find_available_slots`, preserving the
        handout-style data model while reusing the tested datetime-based implementation.
    """

    ##################################################################
    # TODO: Implement as per lab handout requirements and constraints.
    ##################################################################

    if n <= 0:
        return []

    meeting_minutes = duration.total_seconds() / 60
    if meeting_minutes <= 0 or meeting_minutes != int(meeting_minutes):
        raise ValueError("duration must be a positive whole number of minutes.")

    buffer_minutes = buffer.total_seconds() / 60
    if buffer_minutes < 0 or buffer_minutes != int(buffer_minutes):
        raise ValueError("buffer must be a whole number of minutes (>= 0).")

    wh = (
        datetime.combine(day, working_hours.start),
        datetime.combine(day, working_hours.end),
    )

    busy_dt: List[Tuple[datetime, datetime]] = [
        (datetime.combine(day, b.start), datetime.combine(day, b.end)) for b in busy_intervals
    ]

    cw_dt: Optional[Tuple[datetime, datetime]] = None
    if candidate_window is not None:
        cw_dt = (
            datetime.combine(day, candidate_window.start),
            datetime.combine(day, candidate_window.end),
        )

    slots = find_available_slots(
        working_hours=wh,
        busy_intervals=busy_dt,
        meeting_duration=int(meeting_minutes),
        num_slots=n,
        buffer_time=int(buffer_minutes),
        candidate_window=cw_dt,
    )

    return [Slot(start_time=s.time()) for (s, _e) in slots]


def find_available_slots(
    working_hours: Tuple[datetime, datetime],
    busy_intervals: List[Tuple[datetime, datetime]],
    meeting_duration: int,
    num_slots: int,
    buffer_time: int = 0,
    candidate_window: Optional[Tuple[datetime, datetime]] = None,
) -> List[Tuple[datetime, datetime]]:
    """
    Returns a chronologically ordered list of available appointment slots
    that satisfy all constraints.

    Parameters
    ----------
    working_hours : tuple of (start, end) datetime objects.
    busy_intervals : list of (start, end) datetime tuples.
    meeting_duration : int, minutes. Must be > 0.
    num_slots : int, max results. Must be > 0.
    buffer_time : int, minutes gap around busy intervals. Must be >= 0.
    candidate_window : optional (start, end) datetime tuple.

    Returns
    -------
    list of (start, end) datetime tuples, each exactly meeting_duration minutes.
    """

    # ---- Input Validation (C7) ----
    if meeting_duration <= 0:
        raise ValueError("meeting_duration must be greater than 0.")
    if num_slots <= 0:
        raise ValueError("num_slots must be greater than 0.")
    if buffer_time < 0:
        raise ValueError("buffer_time must be 0 or greater.")

    wh_start, wh_end = working_hours
    if wh_start >= wh_end:
        raise ValueError("working_hours start must be strictly before end.")

    if candidate_window is not None:
        cw_start, cw_end = candidate_window
        if cw_start >= cw_end:
            raise ValueError("candidate_window start must be before end.")

    # ---- Determine Effective Window (FR1, C1, C5) ----
    if candidate_window is not None:
        eff_start = max(wh_start, candidate_window[0])
        eff_end = min(wh_end, candidate_window[1])
    else:
        eff_start = wh_start
        eff_end = wh_end

    # If no overlap between working_hours and candidate_window
    if eff_start >= eff_end:
        return []

    duration_td = timedelta(minutes=meeting_duration)
    buffer_td = timedelta(minutes=buffer_time)

    # ---- Normalise Busy Intervals ----
    normalised = []
    for interval in busy_intervals:
        s, e = interval
        if s > e:
            s, e = e, s  # swap reversed intervals
        if s == e:
            continue  # discard zero-length intervals
        normalised.append((s, e))

    # ---- Clip busy intervals to effective window (C9) ----
    clipped = []
    for s, e in normalised:
        cs = max(s, eff_start)
        ce = min(e, eff_end)
        if cs < ce:
            clipped.append((cs, ce))

    # ---- Sort and Merge Overlapping/Adjacent Busy Intervals (FR2, C8) ----
    clipped.sort(key=lambda x: x[0])
    merged: List[Tuple[datetime, datetime]] = []
    for s, e in clipped:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    # ---- Identify Free Gaps ----
    free_gaps: List[Tuple[datetime, datetime]] = []

    if not merged:
        free_gaps.append((eff_start, eff_end))
    else:
        if eff_start < merged[0][0]:
            free_gaps.append((eff_start, merged[0][0]))
        for i in range(len(merged) - 1):
            gap_start = merged[i][1]
            gap_end = merged[i + 1][0]
            if gap_start < gap_end:
                free_gaps.append((gap_start, gap_end))
        if merged[-1][1] < eff_end:
            free_gaps.append((merged[-1][1], eff_end))

    # ---- Apply Buffer and Extract Slots (FR3, FR4, C3) ----
    results: List[Tuple[datetime, datetime]] = []

    for gap_start, gap_end in free_gaps:
        # Determine the buffered start: if this gap follows a busy interval,
        # we need buffer_time after that busy interval.
        slot_start = gap_start
        for bs, be in merged:
            if be == gap_start:
                slot_start = max(slot_start, be + buffer_td)
                break

        # Determine the buffered end: if this gap precedes a busy interval,
        # we need buffer_time before that busy interval.
        slot_end_limit = gap_end
        for bs, be in merged:
            if bs == gap_end:
                slot_end_limit = min(slot_end_limit, bs - buffer_td)
                break

        # Clamp to effective window
        slot_start = max(slot_start, eff_start)
        slot_end_limit = min(slot_end_limit, eff_end)

        # Greedily place slots from slot_start
        current = slot_start
        while current + duration_td <= slot_end_limit:
            results.append((current, current + duration_td))
            if len(results) >= num_slots:
                return results
            current = current + duration_td

    return results