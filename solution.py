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


@dataclass(frozen=True)
class SchedulingDiagnostics:
    """
    Detailed scheduling outcome used to explain why slots were or were not returned.

    `processing_notes` records deterministic normalization actions taken on busy intervals.
    `no_slot_reason` is set only when no valid slots can be produced.
    """

    slots: List[Tuple[datetime, datetime]]
    effective_window: Tuple[datetime, datetime]
    normalized_busy_intervals: List[Tuple[datetime, datetime]]
    processing_notes: List[str]
    no_slot_reason: Optional[str] = None


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

    diagnostics = find_available_slots_with_diagnostics(
        working_hours=working_hours,
        busy_intervals=busy_intervals,
        meeting_duration=meeting_duration,
        num_slots=num_slots,
        buffer_time=buffer_time,
        candidate_window=candidate_window,
    )
    return diagnostics.slots


def find_available_slots_with_diagnostics(
    working_hours: Tuple[datetime, datetime],
    busy_intervals: List[Tuple[datetime, datetime]],
    meeting_duration: int,
    num_slots: int,
    buffer_time: int = 0,
    candidate_window: Optional[Tuple[datetime, datetime]] = None,
) -> SchedulingDiagnostics:
    """
    Returns slot recommendations plus deterministic explanations for normalization
    actions and no-result outcomes.
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

    processing_notes: List[str] = []

    # ---- Determine Effective Window (FR1, C1, C5) ----
    if candidate_window is not None:
        eff_start = max(wh_start, candidate_window[0])
        eff_end = min(wh_end, candidate_window[1])
    else:
        eff_start = wh_start
        eff_end = wh_end

    # If no overlap between working_hours and candidate_window
    if eff_start >= eff_end:
        return SchedulingDiagnostics(
            slots=[],
            effective_window=(eff_start, eff_end),
            normalized_busy_intervals=[],
            processing_notes=["candidate_window does not overlap working_hours"],
            no_slot_reason="candidate_window_outside_working_hours",
        )

    duration_td = timedelta(minutes=meeting_duration)
    buffer_td = timedelta(minutes=buffer_time)

    # ---- Normalise Busy Intervals ----
    normalised = []
    for index, interval in enumerate(busy_intervals):
        s, e = interval
        if s > e:
            processing_notes.append(f"busy_interval[{index}] swapped_reversed_interval")
            s, e = e, s  # swap reversed intervals
        if s == e:
            processing_notes.append(f"busy_interval[{index}] discarded_zero_length_interval")
            continue  # discard zero-length intervals
        normalised.append((s, e))

    # ---- Clip busy intervals to effective window (C9) ----
    clipped = []
    for index, (s, e) in enumerate(normalised):
        cs = max(s, eff_start)
        ce = min(e, eff_end)
        if cs >= ce:
            processing_notes.append(f"normalized_busy_interval[{index}] discarded_outside_effective_window")
            continue
        if cs != s or ce != e:
            processing_notes.append(f"normalized_busy_interval[{index}] clipped_to_effective_window")
        clipped.append((cs, ce))

    # ---- Sort and Merge Overlapping/Adjacent Busy Intervals (FR2, C8) ----
    clipped.sort(key=lambda x: x[0])
    merged: List[Tuple[datetime, datetime]] = []
    for s, e in clipped:
        if merged and s <= merged[-1][1]:
            if s < merged[-1][1]:
                processing_notes.append("merged_overlapping_busy_intervals")
            else:
                processing_notes.append("merged_adjacent_busy_intervals")
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
                return SchedulingDiagnostics(
                    slots=results,
                    effective_window=(eff_start, eff_end),
                    normalized_busy_intervals=merged,
                    processing_notes=processing_notes,
                    no_slot_reason=None,
                )
            current = current + duration_td

    no_slot_reason = _determine_no_slot_reason(
        effective_window=(eff_start, eff_end),
        merged_busy_intervals=merged,
        meeting_duration=duration_td,
        buffer_time=buffer_td,
    )
    return SchedulingDiagnostics(
        slots=results,
        effective_window=(eff_start, eff_end),
        normalized_busy_intervals=merged,
        processing_notes=processing_notes,
        no_slot_reason=no_slot_reason,
    )


def _determine_no_slot_reason(
    effective_window: Tuple[datetime, datetime],
    merged_busy_intervals: List[Tuple[datetime, datetime]],
    meeting_duration: timedelta,
    buffer_time: timedelta,
) -> str:
    """Classifies why no slot could be produced once inputs are validated."""

    eff_start, eff_end = effective_window
    if eff_end - eff_start < meeting_duration:
        return "duration_exceeds_effective_window"

    if not merged_busy_intervals:
        return "no_availability_in_effective_window"

    free_gaps: List[Tuple[datetime, datetime]] = []
    if eff_start < merged_busy_intervals[0][0]:
        free_gaps.append((eff_start, merged_busy_intervals[0][0], False, True))
    for index in range(len(merged_busy_intervals) - 1):
        free_gaps.append(
            (
                merged_busy_intervals[index][1],
                merged_busy_intervals[index + 1][0],
                True,
                True,
            )
        )
    if merged_busy_intervals[-1][1] < eff_end:
        free_gaps.append((merged_busy_intervals[-1][1], eff_end, True, False))

    for gap_start, gap_end, has_left_busy, has_right_busy in free_gaps:
        usable_start = gap_start + (buffer_time if has_left_busy else timedelta(0))
        usable_end = gap_end - (buffer_time if has_right_busy else timedelta(0))
        if usable_end - usable_start >= meeting_duration:
            return "no_availability_in_effective_window"

    return "no_feasible_gap_after_conflicts_and_buffers"
