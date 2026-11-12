"""Provides a thin wrapper around the `ruff` linter."""
import json
import pathlib
import subprocess
import sys
from collections.abc import Sequence

import dataclass_wizard
from pydantic import dataclasses

from hslu.dlm03.tools import unified_diff


@dataclasses.dataclass
class Location:
    """Represents a specific location within a file, identified by column and row.

    Attributes:
        column: The column number (1-indexed).
        row: The row number (1-indexed).
    """
    column: int
    row: int


@dataclasses.dataclass
class Edit:
    """Represents a single textual edit to be applied to a file.

    Attributes:
        content: The new content to insert or replace with.
        location: The starting location of the edit.
        end_location: The ending location of the edit.
    """
    content: str
    location: Location
    end_location: Location

    def to_unified_diff_hunk(self, lines: Sequence[str]) -> unified_diff.UnifiedDiffHunk:
        """Converts this edit into a unified diff hunk for the given file lines."""
        return _edits_to_hunk([self], lines)


def _offset(location: Location, lines: Sequence[str], first_row: int) -> int:
    """Returns the character offset of `location` in the text made of `lines[first_row - 1:]`."""
    if location.row - 1 >= len(lines):
        return sum(len(line) + 1 for line in lines[first_row - 1:])
    return sum(len(line) + 1 for line in lines[first_row - 1:location.row - 1]) + location.column - 1


def _edits_to_hunk(edits: Sequence[Edit], lines: Sequence[str]) -> unified_diff.UnifiedDiffHunk:
    """Applies (non-overlapping) edits to the rows they touch, and returns the corresponding hunk.

    Ruff locations are 1-indexed (row, column) pairs, the end location being exclusive.
    """
    first_row = min(edit.location.row for edit in edits)
    last_row = min(max(edit.end_location.row for edit in edits), len(lines))
    before = list(lines[first_row - 1:last_row])
    segment = "".join(f"{line}\n" for line in before)
    for edit in sorted(edits, key=lambda e: (e.location.row, e.location.column), reverse=True):
        start = _offset(edit.location, lines, first_row)
        end = _offset(edit.end_location, lines, first_row)
        segment = segment[:start] + edit.content + segment[end:]
    after = segment.splitlines()
    return unified_diff.UnifiedDiffHunk(
        from_line=first_row,
        from_count=len(before),
        to_line=first_row,
        to_count=len(after),
        before=before,
        after=after,
    )


@dataclasses.dataclass
class Fix:
    """Represents a suggested fix for an issue, consisting of one or more edits.

    Attributes:
        applicability: A string indicating how applicable the fix is (e.g., "always", "sometimes").
        edits: A sequence of `Edit` objects that constitute the fix.
        message: A human-readable message describing the fix.
    """
    applicability: str
    edits: Sequence[Edit]
    message: str

    def to_unified_diff(self, filename: str, lines: Sequence[str]) -> unified_diff.UnifiedDiff:
        """Converts this fix into a unified diff for the given file lines."""
        # Group the edits touching the same rows, so that each group becomes a single hunk.
        groups: list[list[Edit]] = []
        for edit in sorted(self.edits, key=lambda e: (e.location.row, e.location.column)):
            if groups and edit.location.row <= max(e.end_location.row for e in groups[-1]):
                groups[-1].append(edit)
            else:
                groups.append([edit])
        hunks = []
        delta = 0
        for group in groups:
            hunk = _edits_to_hunk(group, lines)
            hunk.to_line += delta
            delta += hunk.to_count - hunk.from_count
            hunks.append(hunk)
        return unified_diff.UnifiedDiff(
            from_file=f"a/{filename}", from_time=None, to_file=f"b/{filename}", to_time=None, hunks=hunks)


@dataclasses.dataclass
class Issue:
    """Represents a single linting reported issue.

    Attributes:
        filename: The name of the file where the issue was found.
        cell: The cell number if the issue is in a notebook, otherwise None.
        code: The unique code identifying the type of issue (e.g., "E123").
        message: A human-readable description of the issue.
        location: The starting location of the issue.
        end_location: The ending location of the issue.
        noqa_row: The row number where a '# noqa' comment could be placed to ignore this issue.
        url: An optional URL providing more information about the issue.
        fix: An optional `Fix` object suggesting how to resolve the issue.
    """
    filename: str
    cell: int | None
    code: str
    message: str
    location: Location
    end_location: Location
    noqa_row: int
    url: str | None
    fix: Fix | None

    def fix_to_unified_diff(self, content: str) -> unified_diff.UnifiedDiff:
        if self.fix is None:
            return unified_diff.UnifiedDiff(from_file=f"a/{self.filename}", from_time=None,
                                            to_file=f"b/{self.filename}", to_time=None, hunks=[])
        return self.fix.to_unified_diff(self.filename, content.splitlines())


@dataclasses.dataclass
class Issues:
    """A collection of linting issues."""
    issues: list[Issue]


def lint(path: pathlib.Path | str, *, relative: bool = True) -> Issues:
    """Lints a Python file or directory using ruff and returns the found issues.

    Args:
        path: The path to the file or directory to lint.
        relative: Whether to make the reported file names relative to `path` (or to its parent
                  directory when `path` is a file).

    Returns:
        An `Issues` object containing one `Issue` per linting issue.

    Raises:
        RuntimeError: If the ruff process itself fails (e.g., due to configuration issues,
                      or if ruff returns an unexpected exit code other than 0 or 1).
    """
    path = pathlib.Path(path).resolve()
    process = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "ruff", "check", "--output-format=json", str(path)],
        capture_output=True,
        check=False,
    )
    if process.returncode not in {0, 1}:
        raise RuntimeError(process.stderr.decode("utf-8"))
    data = json.loads(process.stdout)
    issues = dataclass_wizard.fromlist(Issue, data)
    if relative:
        root = path if path.is_dir() else path.parent
        for issue in issues:
            filename = pathlib.Path(issue.filename)
            issue.filename = str(filename.relative_to(root))
    return Issues(issues=issues)
