# Copyright 2026 LuigiD5555
# Licensed under the MIT License
# See LICENSE file for details.

"""Strategies for resolving display paths in readable test output."""

from abc import ABC, abstractmethod
from pathlib import Path


class PathResolutionError(ValueError):
    """Raised when a path cannot be resolved relative to the selected base."""


class PathResolutionStrategy(ABC):
    """Contract for resolving a display path for a test file."""

    @abstractmethod
    def resolve_display_path(self, file_path: Path) -> str:
        """
        Return a human-readable relative path for the given file.

        :param file_path: Absolute path of the file to display.
        :raises PathResolutionError: If the file cannot be resolved.
        """
        raise NotImplementedError


class ProjectRootPathStrategy(PathResolutionStrategy):
    """Resolves file paths relative to the project root."""

    def __init__(self, project_root: Path) -> None:
        if not project_root.is_absolute():
            raise ValueError("project_root must be an absolute path.")
        self.project_root = project_root

    def resolve_display_path(self, file_path: Path) -> str:
        try:
            return str(file_path.relative_to(self.project_root))
        except ValueError as error:
            raise PathResolutionError(
                f"File '{file_path}' is outside project root '{self.project_root}'."
            ) from error


class CurrentWorkingDirectoryPathStrategy(PathResolutionStrategy):
    """Resolves file paths relative to the current working directory."""

    def __init__(self, cwd: Path) -> None:
        if not cwd.is_absolute():
            raise ValueError("cwd must be an absolute path.")
        self.cwd = cwd

    def resolve_display_path(self, file_path: Path) -> str:
        try:
            return str(file_path.relative_to(self.cwd))
        except ValueError as error:
            raise PathResolutionError(
                f"File '{file_path}' is outside current working directory '{self.cwd}'."
            ) from error


class ExplicitBasePathStrategy(PathResolutionStrategy):
    """Resolves file paths relative to an explicit base path provided by the user."""

    def __init__(self, base_path: Path) -> None:
        if not base_path.is_absolute():
            raise ValueError("base_path must be an absolute path.")
        self.base_path = base_path

    def resolve_display_path(self, file_path: Path) -> str:
        try:
            return str(file_path.relative_to(self.base_path))
        except ValueError as error:
            raise PathResolutionError(
                f"File '{file_path}' is outside explicit base path '{self.base_path}'."
            ) from error


class AutoPathStrategy(PathResolutionStrategy):
    """Resolves file paths using cwd first, falling back to project root."""

    def __init__(
        self,
        cwd_strategy: CurrentWorkingDirectoryPathStrategy,
        root_strategy: ProjectRootPathStrategy,
    ) -> None:
        self.cwd_strategy = cwd_strategy
        self.root_strategy = root_strategy

    def resolve_display_path(self, file_path: Path) -> str:
        try:
            return self.cwd_strategy.resolve_display_path(file_path)
        except PathResolutionError:
            return self.root_strategy.resolve_display_path(file_path)


class PathStrategyFactory:
    """Builds path resolution strategies based on user configuration."""

    def __init__(self, project_root: Path, cwd: Path) -> None:
        self.project_root = project_root
        self.cwd = cwd

    def build(self, path_mode: str, base_path: str | None = None) -> PathResolutionStrategy:
        """
        Build the requested path resolution strategy.

        :param path_mode: One of ``root``, ``cwd``, ``auto``, ``explicit``.
        :param base_path: Required when path_mode is ``explicit``.
        :raises ValueError: If the configuration is invalid.
        """
        if path_mode == "root":
            return ProjectRootPathStrategy(self.project_root)

        if path_mode == "cwd":
            return CurrentWorkingDirectoryPathStrategy(self.cwd)

        if path_mode == "auto":
            return AutoPathStrategy(
                cwd_strategy=CurrentWorkingDirectoryPathStrategy(self.cwd),
                root_strategy=ProjectRootPathStrategy(self.project_root),
            )

        if path_mode == "explicit":
            if base_path is None:
                raise ValueError("base_path is required when path_mode='explicit'.")
            return ExplicitBasePathStrategy(Path(base_path).resolve())

        raise ValueError(f"Unsupported path_mode: '{path_mode}'. Choose from: root, cwd, auto, explicit.")
