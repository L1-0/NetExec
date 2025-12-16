"""Paginator component for dashboard."""

from dataclasses import dataclass
from typing import TypeVar, Generic, List, Callable, Any

T = TypeVar("T")


@dataclass
class PaginationResult(Generic[T]):
    """Result of a pagination query."""

    items: List[T]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class Paginator(Generic[T]):
    """Generic paginator for dashboard data."""

    def __init__(
        self, data_source: Callable[[int, int, dict], tuple], page_size: int = 20
    ):
        self.data_source = data_source
        self.page_size = page_size
        self.current_page = 1
        self.filters = {}
        self.sort_by = None
        self.sort_desc = False

    def get_page(self, page: int = None) -> PaginationResult[T]:
        """Get a specific page of results."""
        if page is not None:
            self.current_page = max(1, page)

        items, total = self.data_source(self.current_page, self.page_size, self.filters)

        total_pages = max(1, (total + self.page_size - 1) // self.page_size)

        # Adjust current page if out of bounds
        if self.current_page > total_pages:
            self.current_page = total_pages

        return PaginationResult(
            items=items,
            page=self.current_page,
            page_size=self.page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=self.current_page < total_pages,
            has_prev=self.current_page > 1,
        )

    def next_page(self) -> PaginationResult[T]:
        """Navigate to next page."""
        result = self.get_page()
        if result.has_next:
            self.current_page += 1
        return self.get_page()

    def prev_page(self) -> PaginationResult[T]:
        """Navigate to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
        return self.get_page()

    def first_page(self) -> PaginationResult[T]:
        """Go to first page."""
        self.current_page = 1
        return self.get_page()

    def last_page(self) -> PaginationResult[T]:
        """Go to last page."""
        # First get total to know last page
        _, total = self.data_source(1, self.page_size, self.filters)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.current_page = total_pages
        return self.get_page()

    def goto_page(self, page: int) -> PaginationResult[T]:
        """Go to a specific page."""
        return self.get_page(max(1, page))

    def set_filter(self, key: str, value: Any) -> None:
        """Set a filter and reset to first page."""
        self.filters[key] = value
        self.current_page = 1

    def clear_filter(self, key: str) -> None:
        """Remove a specific filter."""
        if key in self.filters:
            del self.filters[key]
            self.current_page = 1

    def clear_filters(self) -> None:
        """Clear all filters and reset to first page."""
        self.filters = {}
        self.current_page = 1

    def set_sort(self, column: str, descending: bool = False) -> None:
        """Set sort column and direction."""
        self.sort_by = column
        self.sort_desc = descending
        self.current_page = 1
