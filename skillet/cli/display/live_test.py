"""Tests for cli/display/live module."""

import pytest

from skillet.cli.display.live import CACHED, FAIL, PASS, PENDING, RUNNING, LiveDisplay


def describe_status_symbols():
    """Tests for status symbol constants."""

    def it_has_all_status_symbols():
        assert PENDING is not None
        assert CACHED is not None
        assert RUNNING is not None
        assert PASS is not None
        assert FAIL is not None

    def it_uses_rich_markup():
        assert "[" in PENDING and "]" in PENDING
        assert "[green]" in PASS
        assert "[red]" in FAIL


def describe_LiveDisplay():
    """Tests for LiveDisplay class."""

    def it_initializes_with_tasks():
        tasks = [
            {"gap_idx": 0, "iteration": 0, "gap_source": "test.yaml"},
            {"gap_idx": 0, "iteration": 1, "gap_source": "test.yaml"},
        ]
        display = LiveDisplay(tasks)
        assert len(display.tasks) == 2
        assert len(display.status) == 2

    def it_creates_pending_status_for_all_tasks():
        tasks = [
            {"gap_idx": 0, "iteration": 0, "gap_source": "a.yaml"},
            {"gap_idx": 1, "iteration": 0, "gap_source": "b.yaml"},
        ]
        display = LiveDisplay(tasks)
        for _key, status in display.status.items():
            assert status["state"] == "pending"
            assert status["result"] is None

    def it_generates_unique_keys_for_tasks():
        tasks = [
            {"gap_idx": 0, "iteration": 0, "gap_source": "test.yaml"},
            {"gap_idx": 0, "iteration": 1, "gap_source": "test.yaml"},
            {"gap_idx": 1, "iteration": 0, "gap_source": "other.yaml"},
        ]
        display = LiveDisplay(tasks)
        keys = list(display.status.keys())
        assert len(keys) == 3
        assert len(set(keys)) == 3  # All unique

    def it_builds_table_with_gap_rows():
        tasks = [
            {"gap_idx": 0, "iteration": 0, "gap_source": "first.yaml"},
            {"gap_idx": 1, "iteration": 0, "gap_source": "second.yaml"},
        ]
        display = LiveDisplay(tasks)
        table = display._build_table()
        assert table.row_count == 2

    @pytest.mark.asyncio
    async def it_updates_task_status():
        tasks = [{"gap_idx": 0, "iteration": 0, "gap_source": "test.yaml"}]
        display = LiveDisplay(tasks)

        await display.update(tasks[0], "running")
        assert display.status["0:0"]["state"] == "running"

        await display.update(tasks[0], "done", {"pass": True})
        assert display.status["0:0"]["state"] == "done"
        result = display.status["0:0"]["result"]
        assert isinstance(result, dict)
        assert result["pass"] is True

    def it_builds_table_with_different_states():
        tasks = [
            {"gap_idx": 0, "iteration": 0, "gap_source": "test.yaml"},
            {"gap_idx": 0, "iteration": 1, "gap_source": "test.yaml"},
            {"gap_idx": 0, "iteration": 2, "gap_source": "test.yaml"},
            {"gap_idx": 0, "iteration": 3, "gap_source": "test.yaml"},
            {"gap_idx": 0, "iteration": 4, "gap_source": "test.yaml"},
        ]
        display = LiveDisplay(tasks)

        # Set different states
        display.status["0:0"] = {"state": "pending", "result": None}
        display.status["0:1"] = {"state": "cached", "result": {"pass": True}}
        display.status["0:2"] = {"state": "running", "result": None}
        display.status["0:3"] = {"state": "done", "result": {"pass": True}}
        display.status["0:4"] = {"state": "done", "result": {"pass": False}}

        table = display._build_table()
        assert table.row_count == 1  # One gap with multiple iterations

    @pytest.mark.asyncio
    async def it_starts_and_stops_display():
        tasks = [{"gap_idx": 0, "iteration": 0, "gap_source": "test.yaml"}]
        display = LiveDisplay(tasks)

        await display.start()
        assert display.live is not None

        await display.stop()
        # Should complete without error

    @pytest.mark.asyncio
    async def it_stops_when_not_started():
        tasks = [{"gap_idx": 0, "iteration": 0, "gap_source": "test.yaml"}]
        display = LiveDisplay(tasks)

        # Should not raise when stopping without starting
        await display.stop()
        assert display.live is None

    @pytest.mark.asyncio
    async def it_updates_live_display_when_running():
        tasks = [{"gap_idx": 0, "iteration": 0, "gap_source": "test.yaml"}]
        display = LiveDisplay(tasks)

        await display.start()
        await display.update(tasks[0], "running")
        await display.update(tasks[0], "done", {"pass": True})
        await display.stop()

    def it_finalize_prints_results(capsys):
        tasks = [
            {"gap_idx": 0, "iteration": 0, "gap_source": "test.yaml"},
            {"gap_idx": 0, "iteration": 1, "gap_source": "test.yaml"},
        ]
        display = LiveDisplay(tasks)

        display.status["0:0"] = {"state": "done", "result": {"pass": True}}
        display.status["0:1"] = {"state": "done", "result": {"pass": False}}

        display.finalize()
        captured = capsys.readouterr()
        assert "test.yaml" in captured.out
        assert "50%" in captured.out

    def it_finalize_shows_cached_results(capsys):
        tasks = [
            {"gap_idx": 0, "iteration": 0, "gap_source": "cached.yaml"},
        ]
        display = LiveDisplay(tasks)

        display.status["0:0"] = {"state": "cached", "result": {"pass": True}}

        display.finalize()
        captured = capsys.readouterr()
        assert "cached.yaml" in captured.out
        assert "100%" in captured.out

    def it_finalize_handles_pending_tasks(capsys):
        tasks = [
            {"gap_idx": 0, "iteration": 0, "gap_source": "pending.yaml"},
        ]
        display = LiveDisplay(tasks)
        # Status stays as pending (default)

        display.finalize()
        captured = capsys.readouterr()
        assert "pending.yaml" in captured.out
        assert "0%" in captured.out
