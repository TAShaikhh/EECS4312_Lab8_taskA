## Student Name: Umer Shaikh
## Student ID: 218 931 790
# Lab 8 – Test Suite
import pytest
from datetime import datetime, timedelta
from solution import find_available_slots


# ---------- Helper ----------
def dt(hour: int, minute: int = 0) -> datetime:
    """Shorthand: returns a datetime on 2025-01-01 at given hour:minute."""
    return datetime(2025, 1, 1, hour, minute)


# ================================================================
# AC1 – No busy intervals, basic slot generation
# Linked: C1, C4, C6, C10
# ================================================================
class TestAC1:
    def test_within_working_hours(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[],
            meeting_duration=30,
            num_slots=2,
        )
        assert result == [(dt(9, 0), dt(9, 30)), (dt(9, 30), dt(10, 0))]

    def test_slot_duration_exact(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[],
            meeting_duration=30,
            num_slots=5,
        )
        for start, end in result:
            assert (end - start) == timedelta(minutes=30)

    def test_max_slots_limit(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[],
            meeting_duration=30,
            num_slots=2,
        )
        assert len(result) <= 2

    def test_deterministic_results(self):
        args = dict(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[],
            meeting_duration=30,
            num_slots=3,
        )
        r1 = find_available_slots(**args)
        r2 = find_available_slots(**args)
        assert r1 == r2


# ================================================================
# AC2 – Buffer time respected around busy intervals
# Linked: C2, C3
# ================================================================
class TestAC2:
    def test_buffer_spacing(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[(dt(10), dt(11))],
            meeting_duration=30,
            num_slots=20,
            buffer_time=15,
        )
        for start, end in result:
            if end <= dt(10):
                assert end <= dt(9, 45)
            if start >= dt(11):
                assert start >= dt(11, 15)

    def test_no_busy_overlap(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[(dt(10), dt(11))],
            meeting_duration=30,
            num_slots=20,
            buffer_time=15,
        )
        for start, end in result:
            assert not (start < dt(11) and end > dt(10))


# ================================================================
# AC3 – Gap too small for meeting
# Linked: C4
# ================================================================
class TestAC3:
    def test_gap_too_small(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[(dt(10), dt(10, 40)), (dt(11), dt(17))],
            meeting_duration=30,
            num_slots=10,
        )
        for start, end in result:
            assert not (start >= dt(10, 40) and end <= dt(11))


# ================================================================
# AC4 – Candidate window clips results
# Linked: C1, C5
# ================================================================
class TestAC4:
    def test_candidate_window_clip(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[],
            meeting_duration=30,
            num_slots=10,
            candidate_window=(dt(13), dt(14)),
        )
        for start, end in result:
            assert start >= dt(13)
            assert end <= dt(14)


# ================================================================
# AC5 – Overlapping busy intervals merged
# Linked: C2, C8
# ================================================================
class TestAC5:
    def test_merged_intervals(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[(dt(10), dt(11)), (dt(10, 30), dt(11, 30))],
            meeting_duration=30,
            num_slots=20,
        )
        for start, end in result:
            assert not (start < dt(11, 30) and end > dt(10))

    def test_unsorted_busy(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[(dt(10, 30), dt(11, 30)), (dt(10), dt(11))],
            meeting_duration=30,
            num_slots=20,
        )
        for start, end in result:
            assert not (start < dt(11, 30) and end > dt(10))


# ================================================================
# AC6 – Busy fills entire day → empty
# Linked: C1, C2
# ================================================================
class TestAC6:
    def test_full_day_busy(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[(dt(9), dt(17))],
            meeting_duration=30,
            num_slots=5,
        )
        assert result == []


# ================================================================
# AC7 – Candidate window outside working hours → empty
# Linked: C5
# ================================================================
class TestAC7:
    def test_external_candidate_window(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[],
            meeting_duration=30,
            num_slots=5,
            candidate_window=(dt(18), dt(20)),
        )
        assert result == []

    def test_no_window_overlap(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[],
            meeting_duration=30,
            num_slots=5,
            candidate_window=(dt(18), dt(20)),
        )
        assert result == []


# ================================================================
# AC8 – Duration longer than available window → empty
# Linked: C1, C4
# ================================================================
class TestAC8:
    def test_duration_longer_than_window(self):
        result = find_available_slots(
            working_hours=(dt(9), dt(9, 30)),
            busy_intervals=[],
            meeting_duration=60,
            num_slots=5,
        )
        assert result == []


# ================================================================
# AC9 – Invalid inputs raise ValueError
# Linked: C7
# ================================================================
class TestAC9:
    def test_invalid_inputs_value_error_duration(self):
        with pytest.raises(ValueError):
            find_available_slots(
                working_hours=(dt(9), dt(17)),
                busy_intervals=[],
                meeting_duration=-1,
                num_slots=5,
            )

    def test_invalid_inputs_value_error_num_slots(self):
        with pytest.raises(ValueError):
            find_available_slots(
                working_hours=(dt(9), dt(17)),
                busy_intervals=[],
                meeting_duration=30,
                num_slots=0,
            )

    def test_invalid_inputs_value_error_buffer(self):
        with pytest.raises(ValueError):
            find_available_slots(
                working_hours=(dt(9), dt(17)),
                busy_intervals=[],
                meeting_duration=30,
                num_slots=5,
                buffer_time=-5,
            )

    def test_invalid_working_hours(self):
        with pytest.raises(ValueError):
            find_available_slots(
                working_hours=(dt(17), dt(9)),
                busy_intervals=[],
                meeting_duration=30,
                num_slots=5,
            )

    def test_invalid_candidate_window(self):
        with pytest.raises(ValueError):
            find_available_slots(
                working_hours=(dt(9), dt(17)),
                busy_intervals=[],
                meeting_duration=30,
                num_slots=5,
                candidate_window=(dt(15), dt(14)),
            )


# ================================================================
# Additional Edge-Case Tests
# ================================================================
class TestEdgeCases:
    def test_clip_busy_to_working_hours(self):
        """C9: Busy intervals extending outside working_hours are clipped."""
        result = find_available_slots(
            working_hours=(dt(9), dt(12)),
            busy_intervals=[(dt(8), dt(10)), (dt(11), dt(18))],
            meeting_duration=30,
            num_slots=10,
        )
        assert result == [(dt(10), dt(10, 30)), (dt(10, 30), dt(11))]

    def test_adjacent_busy_intervals(self):
        """EC2: Adjacent busy intervals are merged."""
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[(dt(10), dt(11)), (dt(11), dt(12))],
            meeting_duration=30,
            num_slots=20,
        )
        for start, end in result:
            assert not (start < dt(12) and end > dt(10))

    def test_reversed_busy_interval_swapped(self):
        """Busy interval with start > end is corrected by swapping."""
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[(dt(11), dt(10))],
            meeting_duration=30,
            num_slots=20,
        )
        for start, end in result:
            assert not (start < dt(11) and end > dt(10))

    def test_zero_length_busy_interval_discarded(self):
        """Busy interval with start == end is discarded."""
        result = find_available_slots(
            working_hours=(dt(9), dt(10)),
            busy_intervals=[(dt(9, 30), dt(9, 30))],
            meeting_duration=30,
            num_slots=2,
        )
        assert result == [(dt(9), dt(9, 30)), (dt(9, 30), dt(10))]

    def test_output_sorted_no_overlaps(self):
        """INV3: Output sorted by start, no internal overlaps."""
        result = find_available_slots(
            working_hours=(dt(9), dt(17)),
            busy_intervals=[(dt(10), dt(11)), (dt(13), dt(14))],
            meeting_duration=30,
            num_slots=20,
        )
        for i in range(len(result) - 1):
            assert result[i][0] < result[i + 1][0]
            assert result[i][1] <= result[i + 1][0]


# ============================================================================
# Legacy tests (copied from `tests.py.bak_20260306_044353`)
# ============================================================================

import pytest
from datetime import date, datetime, time, timedelta

# Update import path to match your project structure:
from solution import TimeWindow, BusyInterval, Slot, suggest_slots


# ---------- Helpers ----------

def combine(d: date, t: time) -> datetime:
    return datetime.combine(d, t)


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def in_window(win: TimeWindow, t: time) -> bool:
    return win.start <= t < win.end


def assert_slots_basic_constraints(
    slots,
    day,
    working_hours,
    busy_intervals,
    duration,
    n,
    buffer,
    candidate_window,
):
    # Return type / length
    assert isinstance(slots, list)
    assert len(slots) <= n

    # Deterministic ordering: start_time ascending
    assert slots == sorted(slots, key=lambda s: s.start_time)

    # Each slot start must be within working_hours and candidate_window (if any)
    for s in slots:
        assert in_window(working_hours, s.start_time)
        if candidate_window is not None:
            assert in_window(candidate_window, s.start_time)

    # Each slot must fit fully inside working_hours and candidate_window
    for s in slots:
        start_dt = combine(day, s.start_time)
        end_dt = start_dt + duration

        wh_end = combine(day, working_hours.end)
        assert end_dt <= wh_end

        if candidate_window is not None:
            cw_end = combine(day, candidate_window.end)
            assert end_dt <= cw_end

    # No overlap with busy intervals, considering buffer:
    # busy interval is expanded to [start-buffer, end+buffer)
    for s in slots:
        slot_start = combine(day, s.start_time)
        slot_end = slot_start + duration

        for b in busy_intervals:
            b_start = combine(day, b.start) - buffer
            b_end = combine(day, b.end) + buffer
            assert not overlaps(slot_start, slot_end, b_start, b_end)


# ---------- Tests ----------

def test_a1_no_busy_simple_slots():
    """
    Like original "single med exact times": here, no busy events.
    Expect earliest slots within working hours (we only assert constraints + non-empty).
    """
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = []
    duration = timedelta(minutes=30)

    out = suggest_slots(
        day=day,
        working_hours=working,
        busy_intervals=busy,
        duration=duration,
        n=3,
        buffer=timedelta(0),
        candidate_window=None
    )

    assert_slots_basic_constraints(out, day, working, busy, duration, 3, timedelta(0), None)
    # Should at least return 1 slot if implementation uses a reasonable slot step
    assert len(out) > 0
    # Earliest slot should be at or after working start
    assert out[0].start_time >= time(9, 0)


def test_a2_deterministic_same_inputs_same_outputs():
    """
    Like original tie/determinism check: same inputs must return identical outputs.
    """
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(17, 0))
    busy = [
        BusyInterval(time(10, 0), time(10, 30)),
        BusyInterval(time(13, 0), time(14, 0)),
    ]
    duration = timedelta(minutes=30)
    buffer = timedelta(minutes=0)

    out1 = suggest_slots(day, working, busy, duration, n=10, buffer=buffer, candidate_window=None)
    out2 = suggest_slots(day, working, busy, duration, n=10, buffer=buffer, candidate_window=None)

    assert [s.start_time for s in out1] == [s.start_time for s in out2]
    assert_slots_basic_constraints(out1, day, working, busy, duration, 10, buffer, None)


def test_a3_overlapping_and_unsorted_busy_intervals_handled():
    """
    Busy intervals may be unsorted/overlapping; suggestions must still avoid conflicts.
    """
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = [
        BusyInterval(time(10, 30), time(11, 0)),
        BusyInterval(time(10, 0), time(10, 45)),   # overlaps with above
        BusyInterval(time(9, 30), time(9, 45)),    # unsorted relative order
    ]
    duration = timedelta(minutes=15)

    out = suggest_slots(day, working, busy, duration, n=8, buffer=timedelta(0), candidate_window=None)
    assert_slots_basic_constraints(out, day, working, busy, duration, 8, timedelta(0), None)


def test_a4_candidate_window_respected():
    """
    Like original allowed_window respected: here we add an extra candidate window restriction.
    """
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(17, 0))
    candidate = TimeWindow(time(13, 0), time(15, 0))
    busy = []
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=5, buffer=timedelta(0), candidate_window=candidate)
    assert_slots_basic_constraints(out, day, working, busy, duration, 5, timedelta(0), candidate)

    # Every slot must start within candidate window
    assert all(candidate.start <= s.start_time < candidate.end for s in out)


def test_a5_buffer_eliminates_small_gaps():
    """
    Like original rate-limit constraint: here buffer is the key extra constraint.
    With buffer, some slots that would otherwise fit should be invalid.
    """
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(11, 0))
    # Two busy intervals leaving a 20-minute gap between them
    busy = [
        BusyInterval(time(9, 30), time(9, 50)),
        BusyInterval(time(10, 10), time(10, 30)),
    ]
    duration = timedelta(minutes=20)

    # Without buffer: the gap 9:50–10:10 is exactly 20 minutes -> potentially valid
    out_no_buffer = suggest_slots(day, working, busy, duration, n=10, buffer=timedelta(0), candidate_window=None)
    assert_slots_basic_constraints(out_no_buffer, day, working, busy, duration, 10, timedelta(0), None)

    # With 5-min buffer: effective busy expands, gap shrinks -> should reduce or remove those slots
    buf = timedelta(minutes=5)
    out_with_buffer = suggest_slots(day, working, busy, duration, n=10, buffer=buf, candidate_window=None)
    assert_slots_basic_constraints(out_with_buffer, day, working, busy, duration, 10, buf, None)

    # Buffer should not increase number of available slots (monotonicity)
    assert len(out_with_buffer) <= len(out_no_buffer)


#################################################################################
# Add your own additional tests here to cover more cases and edge cases as needed.
#################################################################################