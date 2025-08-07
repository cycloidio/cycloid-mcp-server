#!/usr/bin/env python3
"""Script to standardize import organization across the codebase."""

import ast
import re
from pathlib import Path
from typing import List, Tuple


class ImportOrganizer:
    """Organizes imports according to PEP 8 and project standards."""

    STANDARD_LIBRARY_MODULES = {
        "asyncio",
        "functools",
        "inspect",
        "json",
        "os",
        "pathlib",
        "re",
        "tempfile",
        "typing",
        "shlex",
        "importlib",
    }

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = file_path.read_text(encoding="utf-8")

    def organize_imports(self) -> str:
        """Organize imports in the file."""
        lines = self.content.splitlines()

        # Find import section
        import_start = None
        import_end = None

        for i, line in enumerate(lines):
            if line.startswith(("import ", "from ")) and import_start is None:
                import_start = i
            elif (
                import_start is not None
                and not line.startswith(("import ", "from "))
                and line.strip()
            ):
                import_end = i
                break

        if import_start is None:
            return self.content

        if import_end is None:
            import_end = len(lines)

        # Extract imports
        import_lines = lines[import_start:import_end]

        # Categorize imports
        stdlib_imports = []
        third_party_imports = []
        local_imports = []

        for line in import_lines:
            if not line.strip() or line.startswith("#"):
                continue

            if self._is_stdlib_import(line):
                stdlib_imports.append(line)
            elif self._is_local_import(line):
                local_imports.append(line)
            else:
                third_party_imports.append(line)

        # Sort each category
        stdlib_imports.sort()
        third_party_imports.sort()
        local_imports.sort()

        # Rebuild import section
        organized_imports = []

        if stdlib_imports:
            organized_imports.extend(stdlib_imports)

        if third_party_imports:
            if organized_imports:
                organized_imports.append("")
            organized_imports.extend(third_party_imports)

        if local_imports:
            if organized_imports:
                organized_imports.append("")
            organized_imports.extend(local_imports)

        # Rebuild file
        new_lines = (
            lines[:import_start]
            + organized_imports
            + [""]
            + lines[import_end:]  # Empty line after imports
        )

        return "\n".join(new_lines)

    def _is_stdlib_import(self, line: str) -> bool:
        """Check if import is from standard library."""
        # Extract module name
        if line.startswith("import "):
            module = line.split()[1].split(".")[0]
        elif line.startswith("from "):
            module = line.split()[1].split(".")[0]
        else:
            return False

        return module in self.STANDARD_LIBRARY_MODULES

    def _is_local_import(self, line: str) -> bool:
        """Check if import is local to the project."""
        return "src." in line or line.startswith("from .") or line.startswith("from ..")


def main():
    """Organize imports in all Python files."""
    project_root = Path(__file__).parent.parent

    # Find all Python files
    python_files = []
    for pattern in ["src/**/*.py", "tests/**/*.py", "*.py"]:
        python_files.extend(project_root.glob(pattern))

    print(f"Found {len(python_files)} Python files")

    for file_path in python_files:
        if file_path.name == "__init__.py" and file_path.stat().st_size == 0:
            continue  # Skip empty __init__.py files

        try:
            organizer = ImportOrganizer(file_path)
            organized_content = organizer.organize_imports()

            if organized_content != organizer.content:
                print(f"Organizing imports in {file_path.relative_to(project_root)}")
                file_path.write_text(organized_content, encoding="utf-8")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")


if __name__ == "__main__":
    main()
