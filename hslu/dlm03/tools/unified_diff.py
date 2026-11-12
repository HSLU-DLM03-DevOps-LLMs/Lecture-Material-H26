"""Provides classes for parsing and applying unified diff patches."""
import dataclasses
import datetime
import difflib
import html
import pathlib
import re
from collections.abc import Sequence

_UNIFIED_DIFF_HEADER_REGEX = re.compile(
    r"(?P<type>---|\+\+\+) (?P<file>[^\t]*)(?:\t(?P<timestamp>.*))?",
)
_UNIFIED_DIFF_HUNK_HEADER_REGEX = re.compile(
    r"@@ -(?P<from_line>\d+)(?:,(?P<from_count>\d+))? \+(?P<to_line>\d+)(?:,(?P<to_count>\d+))? @@(?: (?:.*))?",
)
_UNIFIED_DIFF_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f %z"


class UnifiedDiffError(Exception):
    """Custom exception for unified diff parsing and applying errors."""


@dataclasses.dataclass
class UnifiedDiffHunk:
    """Represents a single hunk in a unified diff patch."""
    from_line: int
    """The starting line number in the original file."""
    from_count: int
    """The number of lines in the hunk in the original file."""
    to_line: int
    """The starting line number in the new file."""
    to_count: int
    """The number of lines in the hunk in the new file."""
    before: list[str]
    """The lines in the hunk from the original file."""
    after: list[str]
    """The lines in the hunk from the new file."""

    @classmethod
    def from_lines(cls, lines: Sequence[str]) -> "UnifiedDiffHunk":
        """Creates a UnifiedDiffHunk from a sequence of lines.

        Args:
            lines: A sequence of lines representing the hunk.

        Returns:
            A UnifiedDiffHunk object.

        Raises:
            ValueError: If the hunk header is invalid.
            UnifiedDiffError: If a hunk line has an invalid prefix.
        """
        header, lines = lines[0], lines[1:]
        match = _UNIFIED_DIFF_HUNK_HEADER_REGEX.match(header)
        if not match:
            error_message = f"Invalid unified diff hunk header: {header}"
            raise ValueError(error_message)
        from_line = int(match.group("from_line"))
        from_count = (
            int(match.group("from_count"))
            if match.group("from_count") is not None
            else 1
        )
        to_line = int(match.group("to_line"))
        to_count = (
            int(match.group("to_count")) if match.group("to_count") is not None else 1
        )
        before = []
        after = []
        for line in lines:
            if not line:
                # Some tools (and LLMs) strip the leading space of empty context lines.
                before.append("")
                after.append("")
                continue
            prefix, content = line[0], line[1:]
            match prefix:
                case " ":
                    before.append(content)
                    after.append(content)
                case "+":
                    after.append(content)
                case "-":
                    before.append(content)
                case "\\":
                    # "\ No newline at end of file" marker.
                    continue
                case _:
                    error_message = f"Invalid unified diff hunk line prefix: {prefix}"
                    raise UnifiedDiffError(error_message)
        return cls(from_line, from_count, to_line, to_count, before, after)

    @classmethod
    def from_string(cls, string: str) -> "UnifiedDiffHunk":
        """Creates a UnifiedDiffHunk from a string.

        Args:
            string: A string representing the hunk.

        Returns:
            A UnifiedDiffHunk object.
        """
        lines = string.splitlines()
        return cls.from_lines(lines)

    def verify(self, content: Sequence[str], offset: int = 0) -> None:
        """Verifies that the hunk can be applied to the given content.

        Args:
            content: The content to verify against.
            offset: The line offset to apply.

        Raises:
            UnifiedDiffError: If the hunk cannot be applied.
        """
        if len(self.before) != self.from_count:
            error_message = (f"Invalid unified diff hunk: expected {self.from_count} lines before, "
                             f"got {len(self.before)}")
            raise UnifiedDiffError(error_message)
        if len(self.after) != self.to_count:
            error_message = f"Invalid unified diff hunk: expected {self.to_count} lines after, got {len(self.after)}"
            raise UnifiedDiffError(error_message)

        start_index = self.from_line
        if self.from_count > 0:
            start_index -= 1

        start = start_index + offset
        end = start + self.from_count

        before_diff = "\n".join(
            difflib.unified_diff(
                content[start:end],
                self.before,
                n=0,
                fromfile="original",
                tofile="expected",
                lineterm="",
            ),
        )
        if before_diff:
            error_message = ("Cannot apply unified diff on given content, original content does not match expected "
                             f"unified diff content:\n{before_diff}")
            raise UnifiedDiffError(error_message)

    def apply(self, content: list[str], offset: int = 0) -> int:
        """Applies the hunk to the given content.

        Args:
            content: The content to apply the hunk to.
            offset: The line offset to apply.

        Returns:
            The new offset after applying the hunk.
        """
        self.verify(content, offset)
        start_index = self.from_line
        if self.from_count > 0:
            start_index -= 1

        start = start_index + offset
        end = start + self.from_count

        content[start:end] = self.after
        return self.to_count - self.from_count

    def find(self, lines: Sequence[str]) -> "UnifiedDiffHunk":
        """Finds the hunk in the given content.

        Args:
            lines: The content to find the hunk in.

        Returns:
            The hunk in the given content.

        Raises:
            UnifiedDiffError: If the hunk cannot be found.
        """
        matcher = difflib.SequenceMatcher(None, lines, self.before)
        match = matcher.find_longest_match(0, len(lines), 0, len(self.before))
        if match.size != len(self.before):
            error_message = "Could not find hunk in content."
            raise UnifiedDiffError(error_message)
        offset = (match.a + 1) - self.from_line
        return UnifiedDiffHunk(self.from_line + offset, len(self.before), self.to_line + offset, len(self.after),
                               self.before, self.after)


def _unified_diff_header(from_file: str, from_time: datetime.datetime | None, to_file: str,
                         to_time: datetime.datetime | None) -> str:
    from_header = f"--- {from_file}"
    if from_time:
        from_header += f"\t{from_time.strftime(_UNIFIED_DIFF_DATETIME_FORMAT)}"
    to_header = f"+++ {to_file}"
    if to_time:
        to_header += f"\t{to_time.strftime(_UNIFIED_DIFF_DATETIME_FORMAT)}"
    return f"{from_header}\n{to_header}"


@dataclasses.dataclass()
class UnifiedDiff:
    """Represents a UnifiedDiff patch."""
    from_file: str
    """The path to the original file."""
    from_time: datetime.datetime | None
    """The time the original file was last modified."""
    to_file: str
    """The path to the new file."""
    to_time: datetime.datetime | None
    """The time the new file was last modified."""
    hunks: list[UnifiedDiffHunk]
    """A list of hunks in the patch."""

    @classmethod
    def from_string(cls, string: str) -> "UnifiedDiff":
        """Creates a UnifiedDiff from a string.

        Args:
            string: A string representing the unified diff patch.

        Returns:
            A UnifiedDiff object.

        Raises:
            UnifiedDiffError: If the unified diff header is invalid.
        """
        lines = string.splitlines()
        header, lines = lines[:2], lines[2:]
        from_file = None
        from_time = None
        to_file = None
        to_time = None
        for line in header:
            match = _UNIFIED_DIFF_HEADER_REGEX.match(line)
            if not match:
                error_message = f"Invalid unified diff header: {line}"
                raise UnifiedDiffError(error_message)
            header_type = match.group("type")
            match header_type:
                case "---":
                    from_file = match.group("file")
                    timestamp = match.group("timestamp")
                    if timestamp:
                        from_time = datetime.datetime.strptime(timestamp, _UNIFIED_DIFF_DATETIME_FORMAT)
                case "+++":
                    to_file = match.group("file")
                    timestamp = match.group("timestamp")
                    if timestamp:
                        to_time = datetime.datetime.strptime(timestamp, _UNIFIED_DIFF_DATETIME_FORMAT)
                case _:
                    error_message = f"Invalid unified diff header type: {header_type}"
                    raise UnifiedDiffError(error_message)
        hunks = []
        last = None
        for i, line in enumerate(lines):
            if _UNIFIED_DIFF_HUNK_HEADER_REGEX.match(line):
                if last is not None:
                    hunk = UnifiedDiffHunk.from_lines(lines[last:i])
                    hunks.append(hunk)
                last = i
        if last is not None:
            hunk = UnifiedDiffHunk.from_lines(lines[last:])
            hunks.append(hunk)
        if from_file is None:
            from_file = ""
        if to_file is None:
            to_file = ""
        return cls(from_file, from_time, to_file, to_time, hunks)

    def apply(self, content: list[str], *, strict: bool = True) -> list[str]:
        """Applies the patch to the given content.

        Args:
            content: The content to apply the patch to, as a list of lines.
            strict: Whether to apply the patch strictly (`True` by default) or to try to find the hunks in the file.

        Returns:
            The patched content as a list of lines.
        """
        offset = 0
        hunks = self.hunks if strict else [hunk.find(content) for hunk in self.hunks]
        for hunk in hunks:
            offset += hunk.apply(content, offset)
        return content

    def __call__(self, content: str, *, strict: bool = True) -> str:
        """Applies the patch to the given content as a string.

        Args:
            content: The content to apply the patch to, as a string.
            strict: Whether to apply the patch strictly (`True` by default) or to try to find the hunks in the file.

        Returns:
            The patched content as a string. A trailing newline in `content` is preserved (and added when patching
            an empty content, e.g. when creating a new file).
        """
        patched = "\n".join(self.apply(content.splitlines(), strict=strict))
        if patched and (content.endswith("\n") or not content):
            patched += "\n"
        return patched

    def to_string(self) -> str:
        """Converts the UnifiedDiff object back into a unified diff string format."""
        header = _unified_diff_header(self.from_file, self.from_time, self.to_file, self.to_time)
        lines = header.splitlines()
        for hunk in self.hunks:
            hunk_header = f"@@ -{hunk.from_line},{hunk.from_count} +{hunk.to_line},{hunk.to_count} @@"
            lines.append(hunk_header)
            matcher = difflib.SequenceMatcher(None, hunk.before, hunk.after)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                match tag:
                    case "equal":
                        for line in hunk.before[i1:i2]:
                            lines.append(f" {line}")
                    case "delete":
                        for line in hunk.before[i1:i2]:
                            lines.append(f"-{line}")
                    case "insert":
                        for line in hunk.after[j1:j2]:
                            lines.append(f"+{line}")
                    case "replace":
                        for line in hunk.before[i1:i2]:
                            lines.append(f"-{line}")
                        for line in hunk.after[j1:j2]:
                            lines.append(f"+{line}")
        return "\n".join(lines)

    def to_html(self, *, equal_color: str = "#000000ff", insertion_color: str = "#44BB44ff",
                deletion_color: str = "#EE4444ff") -> str:
        """Converts the UnifiedDiff object into an HTML representation with syntax highlighting."""

        def span(color: str, text: str, *, bold: bool = False) -> str:
            weight = " font-weight: bold;" if bold else ""
            return f'<span style="color: {color};{weight} white-space: pre;">{html.escape(text)}</span><br>'

        lines = [
            '<div class="unified-diff" style="font-family: monospace;">',
            span(deletion_color, f"--- {self.from_file}", bold=True),
            span(insertion_color, f"+++ {self.to_file}", bold=True),
        ]
        for hunk in self.hunks:
            hunk_header = f"@@ -{hunk.from_line},{hunk.from_count} +{hunk.to_line},{hunk.to_count} @@"
            lines.append(span(equal_color, hunk_header))

            matcher = difflib.SequenceMatcher(None, hunk.before, hunk.after)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == "equal":
                    lines.extend(span(equal_color, f" {line}") for line in hunk.before[i1:i2])
                if tag in {"delete", "replace"}:
                    lines.extend(span(deletion_color, f"-{line}") for line in hunk.before[i1:i2])
                if tag in {"insert", "replace"}:
                    lines.extend(span(insertion_color, f"+{line}") for line in hunk.after[j1:j2])
        return "\n".join(lines) + "</div>"

    def revert(self) -> "UnifiedDiff":
        """Reverts the patch, returning a new UnifiedDiff that undoes the changes."""
        reverted_hunks = [
            UnifiedDiffHunk(
                from_line=hunk.to_line,
                from_count=hunk.to_count,
                to_line=hunk.from_line,
                to_count=hunk.from_count,
                before=hunk.after,
                after=hunk.before,
            )
            for hunk in self.hunks
        ]
        return UnifiedDiff(
            from_file=self.to_file,
            from_time=self.to_time,
            to_file=self.from_file,
            to_time=self.from_time,
            hunks=reverted_hunks,
        )


def apply(unified_diff: UnifiedDiff, from_file: pathlib.Path | None = None, to_file: pathlib.Path | None = None, *,
          strict: bool = True, cwd: pathlib.Path | None = None) -> None:
    """Applies a unified diff patch to a file.

    Args:
        unified_diff: The unified diff patch to apply.
        from_file: The path to the original file.
        to_file: The path to the new file.
        strict: Whether to apply the patch strictly (`True` by default) or to try to find the hunks in the file.
        cwd: The directory relative paths are resolved against (optional).
    """
    if from_file is None:
        from_file = pathlib.Path(unified_diff.from_file)
    if to_file is None:
        to_file = pathlib.Path(unified_diff.to_file)
    if cwd is not None:
        if not from_file.is_absolute():
            from_file = cwd / from_file
        if not to_file.is_absolute():
            to_file = cwd / to_file
    original_content = from_file.read_text() if from_file.exists() else ""
    patched_content = unified_diff(original_content, strict=strict)
    to_file.parent.mkdir(parents=True, exist_ok=True)
    to_file.write_text(patched_content)


def diff(  # noqa: PLR0913
        from_content: str,
        to_content: str,
        from_file: str | None = None,
        from_time: datetime.datetime | None = None,
        to_file: str | None = None,
        to_time: datetime.datetime | None = None,
        file: str | None = None,
        num_lines: int | None = None,
) -> UnifiedDiff:
    """Computes the unified diff between two strings.

    Args:
        from_content: The original content.
        to_content: The new content.
        from_file: The name of the original file (defaults to `file`).
        from_time: The modification time of the original file.
        to_file: The name of the new file (defaults to `file`).
        to_time: The modification time of the new file.
        file: The file name to use for both sides when `from_file`/`to_file` are not given.
        num_lines: The number of context lines. `None` means the whole file is used as context.

    Returns:
        The `UnifiedDiff` between both contents.
    """
    if from_file is None:
        from_file = file or ""
    if to_file is None:
        to_file = file or ""
    from_lines = from_content.splitlines()
    to_lines = to_content.splitlines()
    n = num_lines if num_lines is not None else max(len(from_lines), len(to_lines))
    unified_diff_lines = list(
        difflib.unified_diff(
            from_lines,
            to_lines,
            fromfile=from_file,
            fromfiledate=from_time.strftime(_UNIFIED_DIFF_DATETIME_FORMAT) if from_time else "",
            tofile=to_file,
            tofiledate=to_time.strftime(_UNIFIED_DIFF_DATETIME_FORMAT) if to_time else "",
            n=n,
            lineterm="",
        ),
    )
    if not unified_diff_lines:
        header = _unified_diff_header(from_file, from_time, to_file, to_time)
        unified_diff_lines = header.splitlines()
        if num_lines is None:
            unified_diff_lines.append(f"@@ -1,{len(from_lines)} +1,{len(from_lines)} @@")
            unified_diff_lines.extend(f" {line}" for line in from_lines)
    diff_string = "\n".join(unified_diff_lines)
    return UnifiedDiff.from_string(diff_string)


def diff_files(from_path: pathlib.Path, to_path: pathlib.Path, num_lines: int | None = None) -> UnifiedDiff:
    """Computes the unified diff between two files."""
    from_content = from_path.read_text()
    to_content = to_path.read_text()
    from_time = datetime.datetime.fromtimestamp(from_path.stat().st_mtime, tz=datetime.UTC)
    to_time = datetime.datetime.fromtimestamp(to_path.stat().st_mtime, tz=datetime.UTC)
    return diff(from_content, to_content, from_file=str(from_path), from_time=from_time, to_file=str(to_path),
                to_time=to_time, num_lines=num_lines)
