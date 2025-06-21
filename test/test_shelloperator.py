"""Unit tests for ShellOperator class using pytest and pytest-mock."""

import logging
import subprocess  # noqa: S404
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from shoper.shelloperator import ShellOperator


class TestShellOperator:
    """Test cases for ShellOperator class."""

    @staticmethod
    def test_init_default_values() -> None:
        """Test ShellOperator initialization with default values."""
        shell_op = ShellOperator()

        assert shell_op.log_txt is None
        assert not shell_op.quiet
        assert not shell_op.clear_log_txt
        assert shell_op.print_command
        assert shell_op.executable == "/bin/bash"
        assert isinstance(shell_op.logger, logging.Logger)

    @staticmethod
    def test_init_with_custom_values() -> None:
        """Test ShellOperator initialization with custom values."""
        with tempfile.NamedTemporaryFile() as tmp:
            log_file = tmp.name
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

    @staticmethod
    def test_post_init_path_conversion() -> None:
        """Test that string log_txt is converted to Path in __post_init__."""
        with tempfile.NamedTemporaryFile() as tmp:
            log_file = tmp.name
        shell_op = ShellOperator(log_txt=log_file)

        # Access private attribute to verify conversion
        assert isinstance(shell_op.log_txt, (str, Path))
        assert str(shell_op.log_txt) == log_file

    @staticmethod
    def test_post_init_clear_log(mocker: MockerFixture) -> None:
        """Test that log file is cleared when clear_log_txt=True."""
        mock_remove = mocker.patch.object(ShellOperator, "_remove_files_or_dirs")

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            ShellOperator(log_txt=tmp.name, clear_log_txt=True)
            mock_remove.assert_called_once_with(Path(tmp.name))

    @staticmethod
    def test_args2list_string() -> None:
        """Test _args2list with string input."""
        result = ShellOperator._args2list("test_command")  # pyright: ignore[reportPrivateUsage]
        assert result == ["test_command"]

    @staticmethod
    def test_args2list_path() -> None:
        """Test _args2list with Path input."""
        path_obj = Path("/test/path")
        result = ShellOperator._args2list(path_obj)  # pyright: ignore[reportPrivateUsage]
        assert result == [path_obj]

    @staticmethod
    def test_args2list_list() -> None:
        """Test _args2list with list input."""
        input_list = ["cmd1", "cmd2"]
        result = ShellOperator._args2list(input_list)  # pyright: ignore[reportPrivateUsage]
        assert result == input_list

    @staticmethod
    def test_args2list_none() -> None:
        """Test _args2list with None input."""
        result = ShellOperator._args2list(None)  # pyright: ignore[reportPrivateUsage]
        assert result == []

    @staticmethod
    def test_args2list_iterable() -> None:
        """Test _args2list with iterable input."""
        result = ShellOperator._args2list(("cmd1", "cmd2"))  # pyright: ignore[reportPrivateUsage]
        assert result == ["cmd1", "cmd2"]

    @staticmethod
    def test_args2pathlist() -> None:
        """Test _args2pathlist method."""
        shell_op = ShellOperator()
        result = shell_op._args2pathlist(["file1.txt", Path("file2.txt")])  # pyright: ignore[reportPrivateUsage]

        expected_count = 2
        assert len(result) == expected_count
        assert all(isinstance(p, Path) for p in result)
        assert str(result[0]) == "file1.txt"
        assert str(result[1]) == "file2.txt"

    @staticmethod
    def test_remove_files_or_dirs_file(mocker: MockerFixture) -> None:
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

        shell_op._remove_files_or_dirs("test_file.txt")  # pyright: ignore[reportPrivateUsage]

        mock_path_constructor.assert_called_once_with(str(mock_path))
        mock_new_path.unlink.assert_called_once()

    @staticmethod
    def test_remove_files_or_dirs_directory(mocker: MockerFixture) -> None:
        """Test _remove_files_or_dirs with a directory."""
        shell_op = ShellOperator()
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.is_dir.return_value = True

        mocker.patch.object(shell_op, "_args2pathlist", return_value=[mock_path])
        mock_rmtree = mocker.patch("shoper.shelloperator.shutil.rmtree")

        shell_op._remove_files_or_dirs("test_dir")  # pyright: ignore[reportPrivateUsage]

        mock_rmtree.assert_called_once_with(str(mock_path))

    @staticmethod
    def test_print_line_with_stdout(
        mocker: MockerFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test _print_line with stdout=True."""
        shell_op = ShellOperator()
        mock_logger = mocker.patch.object(shell_op, "logger")

        shell_op._print_line("test message", stdout=True)  # pyright: ignore[reportPrivateUsage]

        mock_logger.info.assert_called_once_with("test message")
        captured = capsys.readouterr()
        assert "test message" in captured.out

    @staticmethod
    def test_print_line_without_stdout(
        mocker: MockerFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test _print_line with stdout=False."""
        shell_op = ShellOperator()
        mock_logger = mocker.patch.object(shell_op, "logger")

        shell_op._print_line("test message", stdout=False)  # pyright: ignore[reportPrivateUsage]

        mock_logger.info.assert_called_once_with("test message")
        captured = capsys.readouterr()
        assert not captured.out


class TestShellOperatorRun:
    """Test cases for ShellOperator.run method."""

    @staticmethod
    def test_run_skip_if_missing_input() -> None:
        """Test that run skips execution when required input files are missing."""
        shell_op = ShellOperator()

        with pytest.raises(FileNotFoundError) as exc_info:
            shell_op.run("echo test", input_files_or_dirs=["nonexistent_file.txt"])

        assert "input not found" in str(exc_info.value)

    @staticmethod
    def test_run_skip_if_output_exists(mocker: MockerFixture) -> None:
        """Test run skips execution when output files exist and skip_if_exist=True."""
        shell_op = ShellOperator()

        # Mock output files as existing
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mocker.patch.object(shell_op, "_args2pathlist", return_value=[mock_path])

        # Mock _shell_c to ensure it's not called
        mock_shell_c = mocker.patch.object(shell_op, "_shell_c")

        shell_op.run(
            "echo test",
            output_files_or_dirs=["existing_file.txt"],
            skip_if_exist=True,
        )

        mock_shell_c.assert_not_called()

    @staticmethod
    def test_run_remove_previous_outputs(mocker: MockerFixture) -> None:
        """Test that run removes previous outputs when remove_previous=True."""
        shell_op = ShellOperator()

        mock_remove = mocker.patch.object(shell_op, "_remove_files_or_dirs")
        mocker.patch.object(
            shell_op,
            "_shell_c",
            return_value=MagicMock(returncode=0),
        )
        mocker.patch.object(shell_op, "_validate_results")
        mocker.patch.object(shell_op, "_args2list", return_value=["echo test"])

        shell_op.run(
            "echo test",
            output_files_or_dirs=["output.txt"],
            remove_previous=True,
        )

        mock_remove.assert_called_once_with(["output.txt"])

    @staticmethod
    def test_run_synchronous_success(mocker: MockerFixture) -> None:
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

    @staticmethod
    def test_run_synchronous_failure_cleanup(mocker: MockerFixture) -> None:
        """Test that failed synchronous execution triggers cleanup."""
        shell_op = ShellOperator()

        mocker.patch.object(
            shell_op,
            "_shell_c",
            side_effect=subprocess.SubprocessError("Command failed"),
        )
        mock_remove = mocker.patch.object(shell_op, "_remove_files_or_dirs")
        mocker.patch.object(shell_op, "_args2list", return_value=["false"])

        with pytest.raises(subprocess.SubprocessError):
            shell_op.run(
                "false",
                output_files_or_dirs=["output.txt"],
                remove_if_failed=True,
            )

        mock_remove.assert_called_once_with(["output.txt"])

    @staticmethod
    def test_run_asynchronous(mocker: MockerFixture) -> None:
        """Test asynchronous command execution."""
        shell_op = ShellOperator()

        mock_proc = MagicMock()
        mock_popen = mocker.patch.object(shell_op, "_popen", return_value=mock_proc)
        mocker.patch.object(shell_op, "_args2list", return_value=["sleep 1"])

        shell_op.run("sleep 1", output_files_or_dirs=["output.txt"], asynchronous=True)

        mock_popen.assert_called_once()
        # Check that process is added to open_proc_list
        assert len(shell_op._ShellOperator__open_proc_list) == 1  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType,reportUnknownArgumentType]
        assert shell_op._ShellOperator__open_proc_list[0]["procs"] == [mock_proc]  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]

    @staticmethod
    def test_run_with_custom_cwd_and_prompt(mocker: MockerFixture) -> None:
        """Test run with custom working directory and prompt."""
        shell_op = ShellOperator()

        mock_shell_c = mocker.patch.object(
            shell_op,
            "_shell_c",
            return_value=MagicMock(returncode=0),
        )
        mocker.patch.object(shell_op, "_validate_results")
        mocker.patch.object(shell_op, "_args2list", return_value=["pwd"])

        with tempfile.TemporaryDirectory() as tmpdir:
            shell_op.run("pwd", cwd=tmpdir, prompt="[custom] $ ")

        mock_shell_c.assert_called_once()
        call_args = mock_shell_c.call_args[1]
        assert call_args["cwd"] == tmpdir
        assert call_args["prompt"] == "[custom] $ "


class TestShellOperatorWait:
    """Test cases for ShellOperator.wait method."""

    @staticmethod
    def test_wait_no_processes(mocker: MockerFixture) -> None:
        """Test wait method when no processes are running."""
        shell_op = ShellOperator()
        mock_logger = mocker.patch.object(shell_op, "logger")

        shell_op.wait()

        mock_logger.debug.assert_called_once_with("There is no process.")

    @staticmethod
    def test_wait_with_processes(mocker: MockerFixture) -> None:
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
        shell_op._ShellOperator__open_proc_list = [  # pyright: ignore[reportAttributeAccessIssue]
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
        assert shell_op._ShellOperator__open_proc_list == []  # pyright: ignore[reportAttributeAccessIssue]


class TestShellOperatorPopen:
    """Test cases for ShellOperator._popen method."""

    @staticmethod
    def test_popen_with_log_file(mocker: MockerFixture) -> None:
        """Test _popen method with log file configured."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shell_op = ShellOperator(log_txt=tmp.name)

            mock_popen = mocker.patch("shoper.shelloperator.subprocess.Popen")
            mocker.patch("pathlib.Path.open", mocker.mock_open())  # pyright: ignore[reportUnknownMemberType]
            mocker.patch("pathlib.Path.exists", return_value=True)
            mocker.patch.object(shell_op, "_print_line")

            shell_op._popen("echo test", "[test] $ ")  # pyright: ignore[reportPrivateUsage]

            mock_popen.assert_called_once()
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs["args"] == "echo test"
            assert call_kwargs["executable"] == "/bin/bash"
            assert call_kwargs["shell"] is True

    @staticmethod
    def test_popen_without_log_file(mocker: MockerFixture) -> None:
        """Test _popen method without log file."""
        shell_op = ShellOperator()

        mock_popen = mocker.patch("shoper.shelloperator.subprocess.Popen")
        mock_open = mocker.patch("pathlib.Path.open", mocker.mock_open())  # pyright: ignore[reportUnknownMemberType]
        mocker.patch.object(shell_op, "_print_line")

        shell_op._popen("echo test", "[test] $ ")  # pyright: ignore[reportPrivateUsage]

        mock_popen.assert_called_once()
        # Should open /dev/null for output
        mock_open.assert_called_with(mode="w", encoding="utf-8")


class TestShellOperatorShellC:
    """Test cases for ShellOperator._shell_c method."""

    @staticmethod
    def test_shell_c_with_log_quiet(mocker: MockerFixture) -> None:
        """Test _shell_c method with log file and quiet mode."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shell_op = ShellOperator(log_txt=tmp.name, quiet=True)

            mock_popen = mocker.patch("shoper.shelloperator.subprocess.Popen")
            mock_proc = MagicMock()
            mock_proc.poll.return_value = 0  # Process completed
            mock_popen.return_value = mock_proc

            mocker.patch("pathlib.Path.open", mocker.mock_open())  # pyright: ignore[reportUnknownMemberType]
            mocker.patch("pathlib.Path.exists", return_value=True)
            mocker.patch.object(shell_op, "_print_line")

            result = shell_op._shell_c("echo test", "[test] $ ")  # pyright: ignore[reportPrivateUsage]

            assert result == mock_proc
            mock_popen.assert_called_once()

    @staticmethod
    def test_shell_c_no_log_not_quiet(mocker: MockerFixture) -> None:
        """Test _shell_c method without log file and not quiet."""
        shell_op = ShellOperator(quiet=False)

        mock_popen = mocker.patch("shoper.shelloperator.subprocess.Popen")
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc
        mocker.patch.object(shell_op, "_print_line")

        result = shell_op._shell_c("echo test", "[test] $ ")  # pyright: ignore[reportPrivateUsage]

        assert result == mock_proc
        mock_proc.wait.assert_called_once()


class TestShellOperatorValidation:
    """Test cases for ShellOperator validation methods."""

    @staticmethod
    def test_validate_results_success(mocker: MockerFixture) -> None:
        """Test _validate_results with successful processes."""
        shell_op = ShellOperator()

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_validate_outputs = mocker.patch.object(shell_op, "_validate_outputs")

        shell_op._validate_results(  # pyright: ignore[reportPrivateUsage]
            procs=[mock_proc],
            output_files_or_dirs=["output.txt"],
            output_validator=None,
            remove_if_failed=True,
        )

        mock_validate_outputs.assert_called_once_with(
            files_or_dirs=["output.txt"],
            func=None,
            remove_if_failed=True,
        )

    @staticmethod
    def test_validate_results_process_failure(mocker: MockerFixture) -> None:
        """Test _validate_results with failed processes."""
        shell_op = ShellOperator()

        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_remove = mocker.patch.object(shell_op, "_remove_files_or_dirs")

        with pytest.raises(subprocess.SubprocessError) as exc_info:
            shell_op._validate_results(  # pyright: ignore[reportPrivateUsage]
                procs=[mock_proc],
                output_files_or_dirs=["output.txt"],
                remove_if_failed=True,
            )

        assert "Commands returned non-zero exit statuses" in str(exc_info.value)
        mock_remove.assert_called_once_with(["output.txt"])

    @staticmethod
    def test_validate_outputs_success(mocker: MockerFixture) -> None:
        """Test _validate_outputs with existing files."""
        shell_op = ShellOperator()

        mock_path = mocker.patch("shoper.shelloperator.Path")
        mock_path.return_value.exists.return_value = True
        mocker.patch.object(shell_op, "_args2list", return_value=["output.txt"])
        mock_logger = mocker.patch.object(shell_op, "logger")

        shell_op._validate_outputs(["output.txt"])  # pyright: ignore[reportPrivateUsage]

        mock_logger.debug.assert_called_once()

    @staticmethod
    def test_validate_outputs_missing_files(mocker: MockerFixture) -> None:
        """Test _validate_outputs with missing files."""
        shell_op = ShellOperator()

        mock_path = mocker.patch("shoper.shelloperator.Path")
        mock_path.return_value.exists.return_value = False
        mocker.patch.object(shell_op, "_args2list", return_value=["output.txt"])

        with pytest.raises(FileNotFoundError) as exc_info:
            shell_op._validate_outputs(["output.txt"])  # pyright: ignore[reportPrivateUsage]

        assert "output not found" in str(exc_info.value)

    @staticmethod
    def test_validate_outputs_custom_validator_success(
        mocker: MockerFixture,
    ) -> None:
        """Test _validate_outputs with successful custom validator."""
        shell_op = ShellOperator()

        mock_path = mocker.patch("shoper.shelloperator.Path")
        mock_path.return_value.exists.return_value = True
        mocker.patch.object(shell_op, "_args2list", return_value=["output.txt"])
        mock_logger = mocker.patch.object(shell_op, "logger")

        def validator(p: str) -> bool:  # noqa: ARG001
            return True

        shell_op._validate_outputs(["output.txt"], func=validator)  # pyright: ignore[reportPrivateUsage]

        mock_logger.debug.assert_called_once()

    @staticmethod
    def test_validate_outputs_custom_validator_failure(
        mocker: MockerFixture,
    ) -> None:
        """Test _validate_outputs with failed custom validator."""
        shell_op = ShellOperator()

        mock_path = mocker.patch("shoper.shelloperator.Path")
        mock_path.return_value.exists.return_value = True
        mocker.patch.object(shell_op, "_args2list", return_value=["output.txt"])
        mock_remove = mocker.patch.object(shell_op, "_remove_files_or_dirs")

        def validator(p: str) -> bool:  # noqa: ARG001
            return False

        with pytest.raises(RuntimeError) as exc_info:
            shell_op._validate_outputs(  # pyright: ignore[reportPrivateUsage]
                ["output.txt"],
                func=validator,
                remove_if_failed=True,
            )

        assert "output not validated" in str(exc_info.value)
        mock_remove.assert_called_once()


class TestShellOperatorIntegration:
    """Integration tests for ShellOperator."""

    @staticmethod
    def test_real_command_execution() -> None:
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

    @staticmethod
    def test_real_async_execution() -> None:
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

    @staticmethod
    def test_input_validation_real_files() -> None:
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
