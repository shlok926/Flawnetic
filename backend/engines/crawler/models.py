from dataclasses import dataclass

@dataclass
class ElementInfo:
    selector: str           # CSS selector
    element_type: str       # "button" | "input" | "form" | "link" | "dropdown" | "checkbox" | "textarea"
    label: str              # visible text / aria-label / placeholder
    input_type: str | None  # for inputs: "text" | "email" | "number" | "password" | etc.
    is_required: bool
    href: str | None        # for links only

@dataclass
class PageNode:
    url: str
    title: str
    http_status: int
    depth: int
    discovered_via: str     # parent URL or "root"
    screenshot_path: str | None
    elements: list[ElementInfo]

@dataclass
class SiteGraph:
    base_url: str
    pages: list[PageNode]
    total_pages: int
    max_depth_reached: int
    crawl_duration_seconds: float
