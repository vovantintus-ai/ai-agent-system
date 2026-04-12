"""
Shell Tools - Windows compatible (PowerShell + Python execution)
"""

import subprocess
import sys
import io
import contextlib
import os
import platform

BLOCKED_COMMANDS = [
    "rd /s /q C:\\", "format C:", "del /f /s /q C:\\",
    "rm -rf /", "rmdir /s"
]

IS_WINDOWS = platform.system() == "Windows"


class ShellTools:
    def run_command(self, command: str, working_dir: str = None) -> str:
        """Run a shell command (PowerShell on Windows)"""
        for blocked in BLOCKED_COMMANDS:
            if blocked.lower() in command.lower():
                return f"⛔ Blocked dangerous command."

        try:
            cwd = os.path.expanduser(working_dir) if working_dir else os.path.expanduser("~")

            if IS_WINDOWS:
                # Use PowerShell on Windows
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", command],
                    capture_output=True, text=True, timeout=30, cwd=cwd,
                    encoding='utf-8', errors='replace'
                )
            else:
                result = subprocess.run(
                    command, shell=True, capture_output=True,
                    text=True, timeout=30, cwd=cwd
                )

            output = ""
            if result.stdout:
                output += f"Output:\n{result.stdout}"
            if result.stderr:
                output += f"\nErrors:\n{result.stderr}"
            output += f"\nExit code: {result.returncode}"
            return output if output.strip() else "Command executed (no output)"

        except subprocess.TimeoutExpired:
            return "⏱️ Timeout: command took more than 30 seconds"
        except FileNotFoundError:
            return "❌ PowerShell not found. Make sure it's installed."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def run_python(self, code: str) -> str:
        """Execute Python code and capture output"""
        stdout_cap = io.StringIO()
        stderr_cap = io.StringIO()

        safe_globals = {
            "__builtins__": {
                "print": print, "len": len, "range": range,
                "enumerate": enumerate, "zip": zip, "map": map,
                "filter": filter, "list": list, "dict": dict,
                "set": set, "tuple": tuple, "str": str, "int": int,
                "float": float, "bool": bool, "sum": sum, "min": min,
                "max": max, "abs": abs, "round": round,
                "sorted": sorted, "reversed": reversed,
                "isinstance": isinstance, "type": type,
                "Exception": Exception, "ValueError": ValueError,
            }
        }

        try:
            with contextlib.redirect_stdout(stdout_cap), \
                 contextlib.redirect_stderr(stderr_cap):
                exec(code, safe_globals)

            out = stdout_cap.getvalue()
            err = stderr_cap.getvalue()
            result = ""
            if out:
                result += f"Output:\n{out}"
            if err:
                result += f"\nErrors:\n{err}"
            return result if result else "Code executed (no output)"
        except Exception as e:
            return f"❌ Python error: {type(e).__name__}: {str(e)}"
