"""Tests for LiveDisplay class."""

from unittest.mock import PropertyMock, patch

import pytest
from rich.console import Console, ConsoleDimensions

from .live_display import DISPLAY_OVERHEAD, LiveDisplay


def describe_LiveDisplay():
    """Tests for LiveDisplay class."""

    def it_initializes_with_tasks():
        tasks = [
            {"eval_idx": 0, "iteration": 0, "eval_source": "test.yaml"},
            {"eval_idx": 0, "iteration": 1, "eval_source": "test.yaml"},
        ]
        display = LiveDisplay(tasks)
        assert len(display.tasks) == 2
        assert len(display.status) == 2

    def it_creates_pending_status_for_all_tasks():
        tasks = [
            {"eval_idx": 0, "iteration": 0, "eval_source": "a.yaml"},
            {"eval_idx": 1, "iteration": 0, "eval_source": "b.yaml"},
        ]
        display = LiveDisplay(tasks)
        for _key, status in display.status.items():
            assert status["state"] == "pending"
            assert status["result"] is None

    def it_generates_unique_keys_for_tasks():
        tasks = [
            {"eval_idx": 0, "iteration": 0, "eval_source": "test.yaml"},
            {"eval_idx": 0, "iteration": 1, "eval_source": "test.yaml"},
            {"eval_idx": 1, "iteration": 0, "eval_source": "other.yaml"},
        ]
        display = LiveDisplay(tasks)
        keys = list(display.status.keys())
        assert len(keys) == 3
        assert len(set(keys)) == 3  # All unique

    def it_builds_table_with_eval_rows():
        tasks = [
            {"eval_idx": 0, "iteration": 0, "eval_source": "first.yaml"},
            {"eval_idx": 1, "iteration": 0, "eval_source": "second.yaml"},
        ]
        display = LiveDisplay(tasks)
        table = display._build_table()
        assert table.row_count == 2

    @pytest.mark.asyncio
    async def it_updates_task_status():
        tasks = [{"eval_idx": 0, "iteration": 0, "eval_source": "test.yaml"}]
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
            {"eval_idx": 0, "iteration": 0, "eval_source": "test.yaml"},
            {"eval_idx": 0, "iteration": 1, "eval_source": "test.yaml"},
            {"eval_idx": 0, "iteration": 2, "eval_source": "test.yaml"},
            {"eval_idx": 0, "iteration": 3, "eval_source": "test.yaml"},
            {"eval_idx": 0, "iteration": 4, "eval_source": "test.yaml"},
        ]
        display = LiveDisplay(tasks)

        # Set different states
        display.status["0:0"] = {"state": "pending", "result": None}
        display.status["0:1"] = {"state": "cached", "result": {"pass": True}}
        display.status["0:2"] = {"state": "running", "result": None}
        display.status["0:3"] = {"state": "done", "result": {"pass": True}}
        display.status["0:4"] = {"state": "done", "result": {"pass": False}}

        table = display._build_table()
        assert table.row_count == 1  # One eval with multiple iterations

    @pytest.mark.asyncio
    async def it_starts_and_stops_display():
        tasks = [{"eval_idx": 0, "iteration": 0, "eval_source": "test.yaml"}]
        display = LiveDisplay(tasks)

        await display.start()
        assert display.live is not None

        await display.stop()
        # Should complete without error

    @pytest.mark.asyncio
    async def it_stops_when_not_started():
        tasks = [{"eval_idx": 0, "iteration": 0, "eval_source": "test.yaml"}]
        display = LiveDisplay(tasks)

        # Should not raise when stopping without starting
        await display.stop()
        assert display.live is None

    @pytest.mark.asyncio
    async def it_updates_live_display_when_running():
        tasks = [{"eval_idx": 0, "iteration": 0, "eval_source": "test.yaml"}]
        display = LiveDisplay(tasks)

        await display.start()
        await display.update(tasks[0], "running")
        await display.update(tasks[0], "done", {"pass": True})
        await display.stop()

    @patch("skillet.cli.display.live.live_display.get_rate_color", return_value="green")
    def it_shows_percentage_when_all_samples_done(mock_get_rate_color):
        """Test that percentage appears in table when all samples complete."""
        tasks = [
            {"eval_idx": 0, "iteration": 0, "eval_source": "test.yaml"},
            {"eval_idx": 0, "iteration": 1, "eval_source": "test.yaml"},
        ]
        display = LiveDisplay(tasks)

        # Mark all tasks as done
        display.status["0:0"] = {"state": "done", "result": {"pass": True}}
        display.status["0:1"] = {"state": "done", "result": {"pass": False}}

        table = display._build_table()
        # The table should have rich markup for the percentage
        assert table.row_count == 1
        mock_get_rate_color.assert_called_with(50.0)

    @patch("skillet.cli.display.live.live_display.get_rate_color", return_value="green")
    def it_finalize_prints_results(mock_get_rate_color, capsys):
        tasks = [
            {"eval_idx": 0, "iteration": 0, "eval_source": "test.yaml"},
            {"eval_idx": 0, "iteration": 1, "eval_source": "test.yaml"},
        ]
        display = LiveDisplay(tasks)

        display.status["0:0"] = {"state": "done", "result": {"pass": True}}
        display.status["0:1"] = {"state": "done", "result": {"pass": False}}

        display.finalize()
        captured = capsys.readouterr()
        assert "test.yaml" in captured.out
        assert "50%" in captured.out
        mock_get_rate_color.assert_called_with(50.0)

    @patch("skillet.cli.display.live.live_display.get_rate_color", return_value="green")
    def it_finalize_shows_cached_results(mock_get_rate_color, capsys):
        tasks = [
            {"eval_idx": 0, "iteration": 0, "eval_source": "cached.yaml"},
        ]
        display = LiveDisplay(tasks)

        display.status["0:0"] = {"state": "cached", "result": {"pass": True}}

        display.finalize()
        captured = capsys.readouterr()
        assert "cached.yaml" in captured.out
        assert "100%" in captured.out
        mock_get_rate_color.assert_called_with(100.0)

    @patch("skillet.cli.display.live.live_display.get_rate_color", return_value="red")
    def it_finalize_handles_pending_tasks(mock_get_rate_color, capsys):
        tasks = [
            {"eval_idx": 0, "iteration": 0, "eval_source": "pending.yaml"},
        ]
        display = LiveDisplay(tasks)
        # Status stays as pending (default)

        display.finalize()
        captured = capsys.readouterr()
        assert "pending.yaml" in captured.out
        assert "0%" in captured.out
        mock_get_rate_color.assert_called_with(0.0)


def describe_compact_display():
    """Tests for compact display mode."""

    def _make_tasks(eval_count: int, samples: int = 1) -> list[dict]:
        tasks = []
        for i in range(eval_count):
            for s in range(samples):
                tasks.append({"eval_idx": i, "iteration": s, "eval_source": f"eval-{i}.yaml"})
        return tasks

    def _patch_terminal_height(height: int):
        """Mock Rich Console.size for unit tests (curtaincall is for e2e only)."""
        return patch.object(
            Console,
            "size",
            new_callable=PropertyMock,
            return_value=ConsoleDimensions(80, height),
        )

    def it_compacts_when_evals_exceed_terminal_height():
        with _patch_terminal_height(15):
            tasks = _make_tasks(eval_count=15)
            display = LiveDisplay(tasks)
            assert display._should_compact() is True

    def it_uses_detailed_mode_when_evals_fit():
        with _patch_terminal_height(30):
            tasks = _make_tasks(eval_count=5)
            display = LiveDisplay(tasks)
            assert display._should_compact() is False

    def it_compacts_at_exact_boundary():
        """Compacts when evals == available rows + 1."""
        with _patch_terminal_height(10):
            available = 10 - DISPLAY_OVERHEAD
            tasks = _make_tasks(eval_count=available + 1)
            display = LiveDisplay(tasks)
            assert display._should_compact() is True

    def it_builds_compact_table_with_single_row():
        with _patch_terminal_height(10):
            tasks = _make_tasks(eval_count=8, samples=2)
            display = LiveDisplay(tasks)

            display.status["0:0"] = {"state": "done", "result": {"pass": True}}
            display.status["0:1"] = {"state": "done", "result": {"pass": True}}
            display.status["1:0"] = {"state": "done", "result": {"pass": False}}
            display.status["1:1"] = {"state": "running", "result": None}
            display.status["2:0"] = {"state": "cached", "result": {"pass": True}}
            display.status["2:1"] = {"state": "cached", "result": {"pass": False}}
            # Rest stay pending

            table = display._build_table()
            # Compact mode: single summary row instead of 8 eval rows
            assert table.row_count == 1

    @patch("skillet.cli.display.live.live_display.get_rate_color", return_value="green")
    def it_finalize_prints_compact_summary(_mock_rate_color, capsys):
        """finalize() should print a summary line instead of per-eval rows."""
        with _patch_terminal_height(10):
            tasks = _make_tasks(eval_count=8)
            display = LiveDisplay(tasks)

            for key in display.status:
                display.status[key] = {"state": "done", "result": {"pass": True}}

            display.finalize()
            captured = capsys.readouterr()
            assert "8 evals" in captured.out
            # Should NOT contain individual eval filenames
            assert "eval-0.yaml" not in captured.out
