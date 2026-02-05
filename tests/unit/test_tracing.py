"""
Test TracingKit run isolation and file patterns.
"""
import os
import tempfile
from fractal.observability import TracingKit


def test_start_run_generates_run_id():
    """start_run() should generate a unique run_id."""
    kit = TracingKit()
    run_id = kit.start_run()
    assert run_id is not None
    assert len(run_id) == 12  # hex UUID prefix
    assert kit.run_id == run_id


def test_start_run_clears_previous_events():
    """start_run() should clear events from previous runs."""
    kit = TracingKit()
    kit.start_run()
    kit.start_agent("Agent1", "input1")
    kit.end_agent("Agent1", "result1")
    assert len(kit.events) == 2

    # Start new run
    kit.start_run()
    assert len(kit.events) == 0


def test_run_id_attached_to_events():
    """Events should have the current run_id attached."""
    kit = TracingKit()
    run_id = kit.start_run()
    kit.start_agent("Agent1", "input1")
    kit.end_agent("Agent1", "result1")

    for event in kit.events:
        assert event.run_id == run_id


def test_custom_run_id():
    """Custom run_id should be used when provided."""
    kit = TracingKit()
    run_id = kit.start_run(run_id="my-custom-id")
    assert run_id == "my-custom-id"
    assert kit.run_id == "my-custom-id"


def test_end_run_clears_run_id():
    """end_run() should clear the run_id but keep events."""
    kit = TracingKit()
    kit.start_run()
    kit.start_agent("Agent1", "input1")
    kit.end_agent("Agent1", "result1")
    assert len(kit.events) == 2

    kit.end_run()
    assert kit.run_id is None
    assert len(kit.events) == 2  # events preserved


def test_output_file_pattern_with_run_id():
    """Output file pattern should resolve {run_id} placeholder."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern = os.path.join(tmpdir, "trace_{run_id}.jsonl")
        kit = TracingKit(output_file=pattern)

        run_id = kit.start_run()
        expected_path = os.path.join(tmpdir, f"trace_{run_id}.jsonl")
        assert kit.output_file == expected_path


def test_output_file_pattern_with_timestamp():
    """Output file pattern should resolve {timestamp} placeholder."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern = os.path.join(tmpdir, "trace_{timestamp}.jsonl")
        kit = TracingKit(output_file=pattern)

        kit.start_run()
        # Check that timestamp was substituted (not exact match due to timing)
        assert kit.output_file is not None
        assert "{timestamp}" not in kit.output_file
        assert kit.output_file.endswith(".jsonl")


def test_output_file_without_pattern():
    """Without placeholders, output_file should be used as-is."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "trace.jsonl")
        kit = TracingKit(output_file=path)

        kit.start_run()
        assert kit.output_file == path


def test_auto_export_creates_file():
    """Events should be auto-exported to file with run_id pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern = os.path.join(tmpdir, "trace_{run_id}.jsonl")
        kit = TracingKit(output_file=pattern, auto_export=True)

        run_id = kit.start_run()
        kit.start_agent("Agent1", "input1")
        kit.end_agent("Agent1", "result1")
        kit.end_run()

        expected_path = os.path.join(tmpdir, f"trace_{run_id}.jsonl")
        assert os.path.exists(expected_path)

        with open(expected_path, "r") as f:
            lines = f.readlines()
        assert len(lines) == 2


def test_multiple_runs_create_separate_files():
    """Each run() should create a separate trace file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern = os.path.join(tmpdir, "trace_{run_id}.jsonl")
        kit = TracingKit(output_file=pattern, auto_export=True)

        # First run
        run_id_1 = kit.start_run()
        kit.start_agent("Agent1", "input1")
        kit.end_agent("Agent1", "result1")
        kit.end_run()

        # Second run
        run_id_2 = kit.start_run()
        kit.start_agent("Agent2", "input2")
        kit.end_agent("Agent2", "result2")
        kit.end_run()

        # Check both files exist
        file1 = os.path.join(tmpdir, f"trace_{run_id_1}.jsonl")
        file2 = os.path.join(tmpdir, f"trace_{run_id_2}.jsonl")
        assert os.path.exists(file1)
        assert os.path.exists(file2)
        assert run_id_1 != run_id_2


if __name__ == "__main__":
    test_start_run_generates_run_id()
    test_start_run_clears_previous_events()
    test_run_id_attached_to_events()
    test_custom_run_id()
    test_end_run_clears_run_id()
    test_output_file_pattern_with_run_id()
    test_output_file_pattern_with_timestamp()
    test_output_file_without_pattern()
    test_auto_export_creates_file()
    test_multiple_runs_create_separate_files()
    print("All tracing tests passed!")
