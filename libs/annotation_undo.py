# Copyright (c) 2024-2026 LabelCraft
"""Lightweight undo stack for annotation geometry / label edits (not style dialog)."""


class AnnotationUndoStack(object):
    """Stores snapshots of the shape list for Ctrl+Z undo."""

    def __init__(self, max_steps=40):
        self.max_steps = max(1, int(max_steps))
        self._stack = []  # list of (shapes_copy_list, description)

    def clear(self):
        self._stack.clear()

    def __len__(self):
        return len(self._stack)

    def can_undo(self):
        return bool(self._stack)

    def push(self, shapes, description=''):
        """Push a snapshot. `shapes` should already be deep-copied Shape objects."""
        self._stack.append((list(shapes), description or ''))
        while len(self._stack) > self.max_steps:
            self._stack.pop(0)

    def pop(self):
        """Return (shapes, description) or (None, '')."""
        if not self._stack:
            return None, ''
        return self._stack.pop()
