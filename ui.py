"""Multichart grid management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from config import GRID_COLS, GRID_ROWS, VIEWPORT_HEIGHT, VIEWPORT_WIDTH


@dataclass
class GridCell:
    row: int
    col: int


@dataclass
class MultiChartGrid:
    rows: int = GRID_ROWS
    cols: int = GRID_COLS
    viewport_width: int = VIEWPORT_WIDTH
    viewport_height: int = VIEWPORT_HEIGHT
    tabs: Dict[Tuple[int, int], str] = field(default_factory=dict)

    @property
    def cell_width(self) -> float:
        return self.viewport_width / self.cols

    @property
    def cell_height(self) -> float:
        return self.viewport_height / self.rows

    def cell_for_point(self, x: int, y: int) -> Optional[GridCell]:
        if x < 0 or y < 0 or x >= self.viewport_width or y >= self.viewport_height:
            return None
        col = int(x // self.cell_width)
        row = int(y // self.cell_height)
        return GridCell(row=row, col=col)

    def next_empty_cell(self) -> Optional[GridCell]:
        for row in range(self.rows):
            for col in range(self.cols):
                if (row, col) not in self.tabs:
                    return GridCell(row=row, col=col)
        return None

    def assign_tab(self, row: int, col: int, target_id: str) -> None:
        self.tabs[(row, col)] = target_id

    def tab_for_cell(self, row: int, col: int) -> Optional[str]:
        return self.tabs.get((row, col))
