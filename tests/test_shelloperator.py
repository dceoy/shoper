"""Unit tests for ShellOperator class using pytest and pytest-mock."""

import logging
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from shoper.shelloperator import ShellOperator


class TestShellOperator:
    """Test cases for ShellOperator class."""

    def test_init_default_values(self) -> None:
        """Test ShellOperator initialization with default values."""
        shell_op = ShellOperator()

        assert shell_op.log_txt is None
        assert not shell_op.quiet
        assert not shell_op.clear_log_txt
        assert shell_op.print_command
        assert shell_op.executable == "/bin/bash"
        assert isinstance(shell_op.logger, logging.Logger)

    def test_init_with_custom_values(self) -> None:
        """Test ShellOperator initialization with custom values."""
        log_file = "/tmp/test.log"
        shell_op = ShellOperator(
            log_txt=log_file,
            quiet=True,
            clear_log_txt=True,
            print_command=False,
            executable="/bin/sh",
        )

        assert shell_op.log_txt == log_file
        assert shell_op.quiet
        assert shell_op.clear_log_txt
        assert not shell_op.print_command
        assert shell_op.executable == "/bin/sh"

    def test_post_init_path_conversion(self) -> None:
        """Test that string log_txt is converted to Path in __post_init__."""
        log_file = "/tmp/test.log"
        shell_op = ShellOperator(log_txt=log_file)

        # Access private attribute to verify conversion
        assert isinstance(shell_op._ShellOperator__log_txt, Path)
        assert str(shell_op._ShellOperator__log_txt) == log_file

    def test_post_init_clear_log(self, mocker) -> None:
        """Test that log file is cleared when clear_log_txt=True."""
        mock_remove = mocker.patch.object(ShellOperator, "_remove_files_or_dirs")

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shell_op = ShellOperator(log_txt=tmp.name, clear_log_txt=True)
            mock_remove.assert_called_once_with(Path(tmp.name))

    def test_args2list_string(self) -> None:
        """Test _args2list with string input."""
        result = ShellOperator._args2list("test_command")
        assert result == ["test_command"]

    def test_args2list_path(self) -> None:
        """Test _args2list with Path input."""
        path_obj = Path("/test/path")
        result = ShellOperator._args2list(path_obj)
        assert result == [path_obj]

    def test_args2list_list(self) -> None:
        """Test _args2list with list input."""
        input_list = ["cmd1", "cmd2"]
        result = ShellOperator._args2list(input_list)
        assert result == input_list

    def test_args2list_none(self) -> None:
        """Test _args2list with None input."""
        result = ShellOperator._args2list(None)
        assert result == []

    def test_args2list_iterable(self) -> None:
        """Test _args2list with iterable input."""
        result = ShellOperator._args2list(("cmd1", "cmd2"))
        assert result == ["cmd1", "cmd2"]

    def test_args2pathlist(self) -> None:
        """Test _args2pathlist method."""
        shell_op = ShellOperator()
        result = shell_op._args2pathlist(["file1.txt", Path("file2.txt")])

        assert len(result) == 2
        assert all(isinstance(p, Path) for p in result)
        assert str(result[0]) == "file1.txt"
        assert str(result[1]) == "file2.txt"

    def test_remove_files_or_dirs_file(self, mocker) -> None:
        """Test _remove_files_or_dirs with a file."""
        shell_op = ShellOperator()
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.is_dir.return_value = False
        mock_path.exists.return_value = True

        mocker.patch.object(shell_op, "_args2pathlist", return_value=[mock_path])

        # Mock the Path constructor used in the actual implementation
        mock_path_constructor = mocker.patch("shoper.shelloperator.Path")
        mock_new_path = mocker.MagicMock()
        mock_path_constructor.return_value = mock_new_path

        shell_op._remove_files_or_dirs("test_file.txt")

        mock_path_constructor.assert_called_once_with(str(mock_path))
        mock_new_path.unlink.assert_called_once()

    def test_remove_files_or_dirs_directory(self, mocker) -> None:
        """Test _remove_files_or_dirs with a directory."""
        shell_op = ShellOperator()
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.is_dir.return_value = True

        mocker.patch.object(shell_op, "_args2pathlist", return_value=[mock_path])
        mock_rmtree = mocker.patch("shoper.shelloperator.shutil.rmtree")

        shell_op._remove_files_or_dirs("test_dir")

        mock_rmtree.assert_called_once_with(str(mock_path))

    def test_print_line_with_stdout(self, mocker, capsys) -> None:
        """Test _print_line with stdout=True."""
        shell_op = ShellOperator()
        mock_logger = mocker.patch.object(shell_op, "logger")

        shell_op._print_line("test message", stdout=True)

        mock_logger.info.assert_called_once_with("test message")
        captured = capsys.readouterr()
        assert "test message" in captured.out

    def test_print_line_without_stdout(self, mocker, capsys) -> None:
        """Test _print_line with stdout=False."""
        shell_op = ShellOperator()
        mock_logger = mocker.patch.object(shell_op, "logger")

        shell_op._print_line("test message", stdout=False)

        mock_logger.info.assert_called_once_with("test message")
        captured = capsys.readouterr()
        assert captured.out == ""


class TestShellOperatorRun:
    """Test cases for ShellOperator.run method."""

    def test_run_skip_if_missing_input(self) -> None:
        """Test that run skips execution when required input files are missing."""
        shell_op = ShellOperator()

        with pytest.raises(FileNotFoundError) as exc_info:
            shell_op.run("echo test", input_files_or_dirs=["nonexistent_file.txt"])

        assert "input not found" in str(exc_info.value)

    def test_run_skip_if_output_exists(self, mocker) -> None:
        """Test that run skips execution when output files exist and skip_if_exist=True."""
        shell_op = ShellOperator()

        # Mock output files as existing
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mocker.patch.object(shell_op, "_args2pathlist", return_value=[mock_path])

        # Mock _shell_c to ensure it's not called
        mock_shell_c = mocker.patch.object(shell_op, "_shell_c")

        shell_op.run(
            "echo test", output_files_or_dirs=["existing_file.txt"], skip_if_exist=True,
        )

        mock_shell_c.assert_not_called()

    def test_run_remove_previous_outputs(self, mocker) -> None:
        """Test that run removes previous outputs when remove_previous=True."""
        shell_op = ShellOperator()

        mock_remove = mocker.patch.object(shell_op, "_remove_files_or_dirs")
        mock_shell_c = mocker.patch.object(
            shell_op, "_shell_c", return_value=MagicMock(returncode=0),
        )
        mock_validate = mocker.patch.object(shell_op, "_validate_results")
        mocker.patch.object(shell_op, "_args2list", return_value=["echo test"])

        shell_op.run(
            "echo test", output_files_or_dirs=["output.txt"], remove_previous=True,
        )

        mock_remove.assert_called_once_with(["output.txt"])

    def test_run_synchronous_success(self, mocker) -> None:
        """Test successful synchronous command execution."""
        shell_op = ShellOperator()

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_shell_c = mocker.patch.object(shell_op, "_shell_c", return_value=mock_proc)
        mock_validate = mocker.patch.object(shell_op, "_validate_results")
        mocker.patch.object(shell_op, "_args2list", return_value=["echo test"])

        shell_op.run("echo test", output_files_or_dirs=["output.txt"])

        mock_shell_c.assert_called_once()
        mock_validate.assert_called_once_with(
            procs=[mock_proc],
            output_files_or_dirs=["output.txt"],
            output_validator=None,
            remove_if_failed=True,
        )

    def test_run_synchronous_failure_cleanup(self, mocker) -> None:
        """Test that failed synchronous execution triggers cleanup."""
        shell_op = ShellOperator()

        mock_shell_c = mocker.patch.object(
            shell_op,
            "_shell_c",
            side_effect=subprocess.SubprocessError("Command failed"),
        )
        mock_remove = mocker.patch.object(shell_op, "_remove_files_or_dirs")
        mocker.patch.object(shell_op, "_args2list", return_value=["false"])

        with pytest.raises(subprocess.SubprocessError):
            shell_op.run(
                "false", output_files_or_dirs=["output.txt"], remove_if_failed=True,
            )

        mock_remove.assert_called_once_with(["output.txt"])

    def test_run_asynchronous(self, mocker) -> None:
        """Test asynchronous command execution."""
        shell_op = ShellOperator()

        mock_proc = MagicMock()
        mock_popen = mocker.patch.object(shell_op, "_popen", return_value=mock_proc)
        mocker.patch.object(shell_op, "_args2list", return_value=["sleep 1"])

        shell_op.run("sleep 1", output_files_or_dirs=["output.txt"], asynchronous=True)

        mock_popen.assert_called_once()
        # Check that process is added to open_proc_list
        assert len(shell_op._ShellOperator__open_proc_list) == 1
        assert shell_op._ShellOperator__open_proc_list[0]["procs"] == [mock_proc]

    def test_run_with_custom_cwd_and_prompt(self, mocker) -> None:
        """Test run with custom working directory and prompt."""
        shell_op = ShellOperator()

        mock_shell_c = mocker.patch.object(
            shell_op, "_shell_c", return_value=MagicMock(returncode=0),
        )
        mock_validate = mocker.patch.object(shell_op, "_validate_results")
        mocker.patch.object(shell_op, "_args2list", return_value=["pwd"])

        shell_op.run("pwd", cwd="/tmp", prompt="[custom] $ ")

        mock_shell_c.assert_called_once()
        call_args = mock_shell_c.call_args[1]
        assert call_args["cwd"] == "/tmp"
        assert call_args["prompt"] == "[custom] $ "


class TestShellOperatorWait:
    """Test cases for ShellOperator.wait method."""

    def test_wait_no_processes(self, mocker) -> None:
        """Test wait method when no processes are running."""
        shell_op = ShellOperator()
        mock_logger = mocker.patch.object(shell_op, "logger")

        shell_op.wait()

        mock_logger.debug.assert_called_once_with("There is no process.")

    def test_wait_with_processes(self, mocker) -> None:
        """Test wait method with running processes."""
        shell_op = ShellOperator()

        # Mock processes
        mock_proc1 = MagicMock()
        mock_proc1.stdout = MagicMock()
        mock_proc1.stderr = MagicMock()
        mock_proc2 = MagicMock()
        mock_proc2.stdout = None
        mock_proc2.stderr = MagicMock()

        # Set up open_proc_list
        shell_op._ShellOperator__open_proc_list = [
            {
                "procs": [mock_proc1, mock_proc2],
                "output_files_or_dirs": ["output.txt"],
                "output_validator": None,
                "remove_if_failed": True,
            },
        ]

        mock_validate = mocker.patch.object(shell_op, "_validate_results")

        shell_op.wait()

        # Verify processes were waited on
        mock_proc1.wait.assert_called_once()
        mock_proc2.wait.assert_called_once()

        # Verify file handles were closed
        mock_proc1.stdout.close.assert_called_once()
        mock_proc1.stderr.close.assert_called_once()
        mock_proc2.stderr.close.assert_called_once()

        # Verify validation was called
        mock_validate.assert_called_once_with(
            procs=[mock_proc1, mock_proc2],
            output_files_or_dirs=["output.txt"],
            output_validator=None,
            remove_if_failed=True,
        )

        # Verify open_proc_list was cleared
        assert shell_op._ShellOperator__open_proc_list == []


class TestShellOperatorPopen:
    """Test cases for ShellOperator._popen method."""

    def test_popen_with_log_file(self, mocker) -> None:
        """Test _popen method with log file configured."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shell_op = ShellOperator(log_txt=tmp.name)

            mock_popen = mocker.patch("shoper.shelloperator.subprocess.Popen")
            mock_open = mocker.patch("pathlib.Path.open", mocker.mock_open())
            mock_exists = mocker.patch("pathlib.Path.exists", return_value=True)
            mocker.patch.object(shell_op, "_print_line")

            shell_op._popen("echo test", "[test] $ ")

            mock_popen.assert_called_once()
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs["args"] == "echo test"
            assert call_kwargs["executable"] == "/bin/bash"
            assert call_kwargs["shell"] is True

    def test_popen_without_log_file(self, mocker) -> None:
        """Test _popen method without log file."""
        shell_op = ShellOperator()

        mock_popen = mocker.patch("shoper.shelloperator.subprocess.Popen")
        mock_open = mocker.patch("pathlib.Path.open", mocker.mock_open())
        mocker.patch.object(shell_op, "_print_line")

        shell_op._popen("echo test", "[test] $ ")

        mock_popen.assert_called_once()
        # Should open /dev/null for output
        mock_open.assert_called_with(mode="w", encoding="utf-8")


class TestShellOperatorShellC:
    """Test cases for ShellOperator._shell_c method."""

    def test_shell_c_with_log_quiet(self, mocker) -> None:
        """Test _shell_c method with log file and quiet mode."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shell_op = ShellOperator(log_txt=tmp.name, quiet=True)

            mock_popen = mocker.patch("shoper.shelloperator.subprocess.Popen")
            mock_proc = MagicMock()
            mock_proc.poll.return_value = 0  # Process completed
            mock_popen.return_value = mock_proc

            mock_open = mocker.patch("pathlib.Path.open", mocker.mock_open())
            mock_exists = mocker.patch("pathlib.Path.exists", return_value=True)
            mocker.patch.object(shell_op, "_print_line")

            result = shell_op._shell_c("echo test", "[test] $ ")

            assert result == mock_proc
            mock_popen.assert_called_once()

    def test_shell_c_no_log_not_quiet(self, mocker) -> None:
        """Test _shell_c method without log file and not quiet."""
        shell_op = ShellOperator(quiet=False)

        mock_popen = mocker.patch("shoper.shelloperator.subprocess.Popen")
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc
        mocker.patch.object(shell_op, "_print_line")

        result = shell_op._shell_c("echo test", "[test] $ ")

        assert result == mock_proc
        mock_proc.wait.assert_called_once()


class TestShellOperatorValidation:
    """Test cases for ShellOperator validation methods."""

    def test_validate_results_success(self, mocker) -> None:
        """Test _validate_results with successful processes."""
        shell_op = ShellOperator()

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_validate_outputs = mocker.patch.object(shell_op, "_validate_outputs")

        shell_op._validate_results(
            procs=[mock_proc],
            output_files_or_dirs=["output.txt"],
            output_validator=None,
            remove_if_failed=True,
        )

        mock_validate_outputs.assert_called_once_with(
            files_or_dirs=["output.txt"], func=None, remove_if_failed=True,
        )

    def test_validate_results_process_failure(self, mocker) -> None:
        """Test _validate_results with failed processes."""
        shell_op = ShellOperator()

        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_remove = mocker.patch.object(shell_op, "_remove_files_or_dirs")

        with pytest.raises(subprocess.SubprocessError) as exc_info:
            shell_op._validate_results(
                procs=[mock_proc],
                output_files_or_dirs=["output.txt"],
                remove_if_failed=True,
            )

        assert "Commands returned non-zero exit statuses" in str(exc_info.value)
        mock_remove.assert_called_once_with(["output.txt"])

    def test_validate_outputs_success(self, mocker) -> None:
        """Test _validate_outputs with existing files."""
        shell_op = ShellOperator()

        mock_path = mocker.patch("shoper.shelloperator.Path")
        mock_path.return_value.exists.return_value = True
        mocker.patch.object(shell_op, "_args2list", return_value=["output.txt"])
        mock_logger = mocker.patch.object(shell_op, "logger")

        shell_op._validate_outputs(["output.txt"])

        mock_logger.debug.assert_called_once()

    def test_validate_outputs_missing_files(self, mocker) -> None:
        """Test _validate_outputs with missing files."""
        shell_op = ShellOperator()

        mock_path = mocker.patch("shoper.shelloperator.Path")
        mock_path.return_value.exists.return_value = False
        mocker.patch.object(shell_op, "_args2list", return_value=["output.txt"])

        with pytest.raises(FileNotFoundError) as exc_info:
            shell_op._validate_outputs(["output.txt"])

        assert "output not found" in str(exc_info.value)

    def test_validate_outputs_custom_validator_success(self, mocker) -> None:
        """Test _validate_outputs with successful custom validator."""
        shell_op = ShellOperator()

        mock_path = mocker.patch("shoper.shelloperator.Path")
        mock_path.return_value.exists.return_value = True
        mocker.patch.object(shell_op, "_args2list", return_value=["output.txt"])
        mock_logger = mocker.patch.object(shell_op, "logger")

        validator = lambda p: True
        shell_op._validate_outputs(["output.txt"], func=validator)

        mock_logger.debug.assert_called_once()

    def test_validate_outputs_custom_validator_failure(self, mocker) -> None:
        """Test _validate_outputs with failed custom validator."""
        shell_op = ShellOperator()

        mock_path = mocker.patch("shoper.shelloperator.Path")
        mock_path.return_value.exists.return_value = True
        mocker.patch.object(shell_op, "_args2list", return_value=["output.txt"])
        mock_remove = mocker.patch.object(shell_op, "_remove_files_or_dirs")

        validator = lambda p: False
        with pytest.raises(RuntimeError) as exc_info:
            shell_op._validate_outputs(
                ["output.txt"], func=validator, remove_if_failed=True,
            )

        assert "output not validated" in str(exc_info.value)
        mock_remove.assert_called_once()


class TestShellOperatorIntegration:
    """Integration tests for ShellOperator."""

    def test_real_command_execution(self) -> None:
        """Test real command execution with actual subprocess."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test_output.txt"
            shell_op = ShellOperator(quiet=True)

            shell_op.run(
                f"echo 'Hello World' > {output_file}",
                output_files_or_dirs=[str(output_file)],
            )

            assert output_file.exists()
            assert "Hello World" in output_file.read_text()

    def test_real_async_execution(self) -> None:
        """Test real asynchronous command execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "async_output.txt"
            shell_op = ShellOperator(quiet=True)

            shell_op.run(
                f"sleep 0.1 && echo 'Async Hello' > {output_file}",
                output_files_or_dirs=[str(output_file)],
                asynchronous=True,
            )

            # File shouldn't exist immediately
            assert not output_file.exists()

            # Wait for completion
            shell_op.wait()

            # Now file should exist
            assert output_file.exists()
            assert "Async Hello" in output_file.read_text()

    def test_input_validation_real_files(self) -> None:
        """Test input validation with real files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.txt"
            input_file.write_text("test content")

            shell_op = ShellOperator(quiet=True)

            # This should succeed
            shell_op.run(f"cat {input_file}", input_files_or_dirs=[str(input_file)])

            # This should fail
            with pytest.raises(FileNotFoundError):
                shell_op.run(
                    "echo test",
                    input_files_or_dirs=[str(Path(tmpdir) / "nonexistent.txt")],
                )
