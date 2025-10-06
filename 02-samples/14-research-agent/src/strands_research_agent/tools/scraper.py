"""BeautifulSoup4 tool for comprehensive HTML/XML parsing and web scraping.
Provides full access to BeautifulSoup4's capabilities including parsing,
searching, navigating, and modifying HTML/XML documents.
"""

import json
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table
from rich.tree import Tree
from strands import tool

console = Console()


def clean_text(text: Any) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    if isinstance(text, Tag):
        text = text.get_text()
    if not isinstance(text, str):
        text = str(text)
    # Remove extra whitespace and normalize
    return " ".join(text.split())


def get_tag_text(tag: Tag) -> str:
    """Get clean text from a tag."""
    return clean_text(tag.string if tag else "")


def extract_element_data(element: Tag) -> dict:
    """Extract relevant data from a BS4 element."""
    if not element or not isinstance(element, Tag):
        return None

    data = {
        "tag": element.name,
        "text": clean_text(element.get_text()),
        "html": str(element),
    }
    if element.attrs:
        data["attributes"] = dict(element.attrs)
    return data


def create_element_tree(element: Tag, tree: Tree) -> None:
    """Create a tree visualization of HTML structure."""
    if not isinstance(element, Tag):
        return

    # Create node label with tag name and classes
    classes = element.get("class", [])
    class_str = f" .{'.'.join(classes)}" if classes else ""
    id_str = f" #{element['id']}" if element.get("id") else ""
    label = f"{element.name}{class_str}{id_str}"

    # Add text preview if it exists
    text = clean_text(element.string)
    if text:
        label += f": {text[:30]}..." if len(text) > 30 else f": {text}"

    # Create branch
    branch = tree.add(label)

    # Recursively add children
    for child in element.children:
        if isinstance(child, Tag):
            create_element_tree(child, branch)


@tool
def scraper(
    action: str,
    content: str | None = None,
    url: str | None = None,
    parser: str = "html.parser",
    find_params: dict[str, Any] | None = None,
    navigation: dict[str, Any] | None = None,
    modifications: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Advanced HTML/XML parsing and web scraping tool using BeautifulSoup4.

    This tool provides comprehensive HTML/XML parsing and web scraping capabilities
    using BeautifulSoup4. It supports various actions like parsing, finding elements,
    extracting text, modifying content, and navigating document structures.

    Args:
        action: The BeautifulSoup action to perform. One of:
            - "parse": Parse HTML/XML content
            - "find": Find elements using various methods
            - "extract_text": Extract text from elements
            - "extract_attrs": Extract attributes from elements
            - "modify": Modify HTML content
            - "navigate": Navigate through document tree
            - "scrape_url": Scrape content from URL
        content: HTML/XML content to parse (for parse/modify actions)
        url: URL to scrape (for scrape_url action)
        parser: Parser to use (default: html.parser). Options: html.parser, lxml, xml, html5lib
        find_params: Parameters for find/find_all operations
        navigation: Navigation parameters
        modifications: List of modifications to apply. Each modification requires a CSS selector as target.

    Returns:
        Dict containing status and response content:
        {
            "status": "success|error",
            "content": [{"text": "Response message"}]
        }
    """
    # Set default values for optional parameters
    if find_params is None:
        find_params = {}
    if navigation is None:
        navigation = {}
    if modifications is None:
        modifications = []

    try:
        if action == "scrape_url":
            if not url:
                raise ValueError("URL is required for scrape_url action")
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            console.print(Panel.fit(f"[bold blue]Scraping URL: {url}", style="blue"))

            with Progress() as progress:
                # Initialize progress tasks
                fetch_task = progress.add_task("[green]Fetching URL...", total=100)
                parse_task = progress.add_task(
                    "[cyan]Parsing content...", total=100, visible=False
                )
                analyze_task = progress.add_task(
                    "[yellow]Analyzing elements...", total=100, visible=False
                )

                try:
                    # Fetch URL
                    response = requests.get(
                        url, headers=headers, timeout=10, verify=True
                    )
                    response.raise_for_status()
                    content = response.text
                    progress.update(fetch_task, completed=100)

                    # Parse content
                    progress.update(parse_task, visible=True)
                    soup = BeautifulSoup(content, parser)
                    progress.update(parse_task, advance=50)

                    # Create document overview
                    title = get_tag_text(soup.find("title"))
                    console.print(f"\n[bold cyan]Document Title:[/] {title}")

                    # Extract meta information
                    meta_tags = {
                        tag.get("name", tag.get("property", "")): tag.get("content", "")
                        for tag in soup.find_all("meta")
                        if tag.get("name") or tag.get("property")
                    }

                    if meta_tags:
                        meta_table = Table(
                            show_header=True, header_style="bold magenta"
                        )
                        meta_table.add_column("Meta Property")
                        meta_table.add_column("Content")
                        for prop, content in meta_tags.items():
                            if content:  # Only show non-empty meta tags
                                meta_table.add_row(
                                    prop,
                                    (
                                        content[:100] + "..."
                                        if len(content) > 100
                                        else content
                                    ),
                                )
                        console.print("\n[bold cyan]Meta Information:[/]")
                        console.print(meta_table)

                    progress.update(parse_task, completed=100)

                    # Analyze elements
                    progress.update(analyze_task, visible=True)

                    # Extract and display links
                    links = [
                        {"href": link.get("href"), "text": clean_text(link.text)}
                        for link in soup.find_all("a", href=True)
                    ]
                    progress.update(analyze_task, advance=25)

                    if links:
                        link_table = Table(
                            show_header=True, header_style="bold magenta"
                        )
                        link_table.add_column("Link Text")
                        link_table.add_column("URL")
                        for link in links[:10]:  # Show first 10 links
                            link_table.add_row(
                                (
                                    link["text"][:50] + "..."
                                    if len(link["text"]) > 50
                                    else link["text"]
                                ),
                                link["href"],
                            )
                        console.print("\n[bold cyan]Links Found:[/] (showing first 10)")
                        console.print(link_table)

                    # Extract and display headings
                    headings = [
                        {"level": int(h.name[1]), "text": clean_text(h.text)}
                        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
                    ]
                    progress.update(analyze_task, advance=25)

                    if headings:
                        heading_tree = Tree("[bold cyan]📑 Document Structure[/]")
                        current_level = 0
                        current_node = heading_tree
                        for h in headings:
                            level = h["level"]
                            text = h["text"]
                            if level > current_level:
                                current_node = current_node.add(
                                    f"[bold]H{level}:[/] {text}"
                                )
                            else:
                                current_node = heading_tree.add(
                                    f"[bold]H{level}:[/] {text}"
                                )
                            current_level = level
                        console.print("\n")
                        console.print(heading_tree)

                    # Extract and display images
                    images = [
                        {"src": img.get("src"), "alt": img.get("alt", "")}
                        for img in soup.find_all("img", src=True)
                    ]
                    progress.update(analyze_task, advance=25)

                    if images:
                        image_table = Table(
                            show_header=True, header_style="bold magenta"
                        )
                        image_table.add_column("Image Source")
                        image_table.add_column("Alt Text")
                        for img in images:
                            image_table.add_row(
                                img["src"], img["alt"] or "[grey](no alt text)"
                            )
                        console.print("\n[bold cyan]Images Found:[/]")
                        console.print(image_table)

                    # Show text preview
                    text_content = clean_text(soup.get_text(separator=" "))
                    text_preview = (
                        text_content[:200] + "..."
                        if len(text_content) > 200
                        else text_content
                    )
                    console.print("\n[bold cyan]Text Preview:[/]")
                    console.print(Panel(text_preview, style="green"))

                    progress.update(analyze_task, completed=100)

                    # Create final result
                    result = {
                        "url": url,
                        "status_code": response.status_code,
                        "content_type": response.headers.get("content-type", ""),
                        "title": title,
                        "text": text_content,
                        "meta": meta_tags,
                        "links": links,
                        "headings": headings,
                        "images": images,
                    }

                    # Show statistics
                    stats_table = Table(show_header=True, header_style="bold magenta")
                    stats_table.add_column("Element Type")
                    stats_table.add_column("Count")

                    stats_table.add_row("Links", str(len(links)))
                    stats_table.add_row("Headings", str(len(headings)))
                    stats_table.add_row("Images", str(len(images)))
                    stats_table.add_row("Meta Tags", str(len(meta_tags)))

                    console.print("\n[bold cyan]Page Statistics:[/]")
                    console.print(stats_table)

                    console.print("\n[bold green]✓ Scraping complete![/]")

                    return {
                        "status": "success",
                        "content": [
                            {"text": f"Successfully scraped {url}"},
                            {"text": f"Results: {json.dumps(result, indent=2)}"},
                        ],
                    }
                except requests.RequestException as e:
                    raise ValueError(f"Failed to fetch URL: {str(e)}")
        else:
            if not content and action != "scrape_url":
                raise ValueError("Content is required for this action")
            soup = BeautifulSoup(content, parser)
            result = None

        if action == "parse":
            console.print(Panel.fit("[bold blue]Parsing HTML Document", style="blue"))

            with Progress() as progress:
                parse_task = progress.add_task(
                    "[green]Analyzing document structure...", total=100
                )

                # Parse title
                progress.update(parse_task, advance=10)
                title_tag = soup.find("title")
                title = get_tag_text(title_tag)
                console.print(f"\n[bold cyan]Document Title:[/] {title}")

                # Create document tree
                progress.update(parse_task, advance=20)
                console.print("\n[bold cyan]Document Structure:[/]")
                doc_tree = Tree("🌐 HTML Document")
                create_element_tree(soup.find("html"), doc_tree)
                console.print(doc_tree)

                # Parse links
                progress.update(parse_task, advance=20)
                links = [
                    {"href": link.get("href"), "text": clean_text(link.text)}
                    for link in soup.find_all("a", href=True)
                ]

                if links:
                    link_table = Table(show_header=True, header_style="bold magenta")
                    link_table.add_column("Link Text")
                    link_table.add_column("URL")
                    for link in links:
                        link_table.add_row(
                            (
                                link["text"][:50] + "..."
                                if len(link["text"]) > 50
                                else link["text"]
                            ),
                            link["href"],
                        )
                    console.print("\n[bold cyan]Links Found:[/]")
                    console.print(link_table)

                # Parse headings
                progress.update(parse_task, advance=20)
                headings = [
                    {"level": int(h.name[1]), "text": clean_text(h.text)}
                    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
                ]

                if headings:
                    heading_table = Table(show_header=True, header_style="bold magenta")
                    heading_table.add_column("Level")
                    heading_table.add_column("Heading Text")
                    for h in headings:
                        heading_table.add_row(f"H{h['level']}", h["text"])
                    console.print("\n[bold cyan]Document Headings:[/]")
                    console.print(heading_table)

                # Parse lists
                progress.update(parse_task, advance=20)
                lists = [
                    {
                        "type": ul.name,
                        "items": [clean_text(li.text) for li in ul.find_all("li")],
                    }
                    for ul in soup.find_all(["ul", "ol"])
                ]

                if lists:
                    console.print("\n[bold cyan]Lists Found:[/]")
                    for lst in lists:
                        list_panel = Panel.fit(
                            "\n".join([f"• {item}" for item in lst["items"]]),
                            title=f"{lst['type'].upper()} List",
                            style="green",
                        )
                        console.print(list_panel)

                # Complete progress
                progress.update(parse_task, advance=10)

            result = {
                "title": title,
                "text": clean_text(soup.get_text(separator=" ")),
                "links": links,
                "structure": {
                    "headings": headings,
                    "paragraphs": [
                        clean_text(p.text) for p in soup.find_all("p") if p.text.strip()
                    ],
                    "lists": lists,
                },
            }

            console.print("\n[bold green]✓ Parsing complete![/]")

        elif action == "find":
            console.print(Panel.fit("[bold blue]Finding Elements", style="blue"))

            # find_params is now a direct parameter (no need to extract)

            # Show search parameters
            search_table = Table(show_header=True, header_style="bold magenta")
            search_table.add_column("Parameter")
            search_table.add_column("Value")

            if "selector" in find_params:
                search_table.add_row("CSS Selector", find_params["selector"])
            else:
                for param, value in find_params.items():
                    if value is not None:
                        search_table.add_row(param, str(value))

            console.print("\n[bold cyan]Search Parameters:[/]")
            console.print(search_table)

            with Progress() as progress:
                find_task = progress.add_task(
                    "[green]Searching for elements...", total=100
                )

                # Find elements
                progress.update(find_task, advance=40)
                if "selector" in find_params:
                    elements = soup.select(find_params["selector"])
                else:
                    name = find_params.get("name")
                    attrs = find_params.get("attrs", {})
                    recursive = find_params.get("recursive", True)
                    string = find_params.get("string")
                    limit = find_params.get("limit")

                    elements = soup.find_all(
                        name=name,
                        attrs=attrs,
                        recursive=recursive,
                        string=string,
                        limit=limit,
                    )

                # Process results
                progress.update(find_task, advance=40)
                result = [
                    extract_element_data(el) for el in elements if isinstance(el, Tag)
                ]

                # Show results
                if result:
                    console.print(f"\n[bold green]✓ Found {len(result)} element(s)[/]")

                    # Create results table
                    results_table = Table(show_header=True, header_style="bold magenta")
                    results_table.add_column("Tag")
                    results_table.add_column("Attributes")
                    results_table.add_column("Text Preview")

                    for item in result:
                        tag = item["tag"]
                        attrs = json.dumps(item.get("attributes", {}), indent=2)
                        text = (
                            item.get("text", "")[:50] + "..."
                            if item.get("text", "")
                            else ""
                        )

                        results_table.add_row(f"[bold]{tag}[/]", attrs, text)

                    console.print("\n[bold cyan]Found Elements:[/]")
                    console.print(results_table)
                else:
                    console.print(
                        "\n[bold yellow]! No elements found matching the criteria[/]"
                    )

                # Complete progress
                progress.update(find_task, advance=20)

            console.print("\n[bold green]✓ Search complete![/]")

        elif action == "extract_text":
            console.print(Panel.fit("[bold blue]Extracting Text Content", style="blue"))

            with Progress() as progress:
                extract_task = progress.add_task(
                    "[green]Processing text content...", total=100
                )

                # Extract full text
                progress.update(extract_task, advance=25)
                full_text = clean_text(soup.get_text(separator=" "))
                console.print("\n[bold cyan]Full Text Preview:[/]")
                console.print(
                    Panel(
                        full_text[:200] + "..." if len(full_text) > 200 else full_text,
                        style="green",
                    )
                )

                # Extract stripped strings
                progress.update(extract_task, advance=25)
                stripped_strings = [clean_text(s) for s in soup.stripped_strings]

                # Extract structured text
                progress.update(extract_task, advance=25)
                headings = [
                    clean_text(h.text)
                    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
                ]
                paragraphs = [clean_text(p.text) for p in soup.find_all("p")]
                lists = [clean_text(li.text) for li in soup.find_all("li")]

                # Show structured content
                if headings:
                    heading_tree = Tree("[bold cyan]📑 Headings[/]")
                    for h in headings:
                        heading_tree.add(h)
                    console.print("\n")
                    console.print(heading_tree)

                if paragraphs:
                    console.print("\n[bold cyan]📝 Paragraphs:[/]")
                    for i, p in enumerate(paragraphs, 1):
                        preview = p[:100] + "..." if len(p) > 100 else p
                        console.print(f"{i}. {preview}")

                if lists:
                    list_tree = Tree("[bold cyan]📋 List Items[/]")
                    for item in lists:
                        list_tree.add(item)
                    console.print("\n")
                    console.print(list_tree)

                # Create result
                result = {
                    "full_text": full_text,
                    "stripped_strings": stripped_strings,
                    "structured_text": {
                        "headings": headings,
                        "paragraphs": paragraphs,
                        "lists": lists,
                    },
                }

                # Complete progress
                progress.update(extract_task, advance=25)

            # Show statistics
            stats_table = Table(show_header=True, header_style="bold magenta")
            stats_table.add_column("Content Type")
            stats_table.add_column("Count")
            stats_table.add_column("Total Length")

            stats_table.add_row(
                "Headings", str(len(headings)), str(sum(len(h) for h in headings))
            )
            stats_table.add_row(
                "Paragraphs", str(len(paragraphs)), str(sum(len(p) for p in paragraphs))
            )
            stats_table.add_row(
                "List Items", str(len(lists)), str(sum(len(li) for li in lists))
            )

            console.print("\n[bold cyan]Content Statistics:[/]")
            console.print(stats_table)

            console.print("\n[bold green]✓ Text extraction complete![/]")

        elif action == "extract_attrs":
            console.print(
                Panel.fit("[bold blue]Extracting Element Attributes", style="blue")
            )

            with Progress() as progress:
                attr_task = progress.add_task("[green]Analyzing elements...", total=100)

                # Find all elements with attributes
                progress.update(attr_task, advance=30)
                elements = soup.find_all(True)
                elements_with_attrs = [el for el in elements if el.attrs]

                # Process attributes
                progress.update(attr_task, advance=40)
                result = []
                attr_stats = {}

                for el in elements_with_attrs:
                    attr_data = {
                        "tag": el.name,
                        "attributes": dict(el.attrs),
                        "text": clean_text(el.text) if el.text.strip() else None,
                    }
                    result.append(attr_data)

                    # Collect statistics
                    for attr in el.attrs:
                        if attr not in attr_stats:
                            attr_stats[attr] = {"count": 0, "tags": set()}
                        attr_stats[attr]["count"] += 1
                        attr_stats[attr]["tags"].add(el.name)

                # Show results
                if result:
                    console.print(
                        f"\n[bold green]✓ Found {len(result)} elements with attributes[/]"
                    )

                    # Create attribute summary table
                    attr_table = Table(show_header=True, header_style="bold magenta")
                    attr_table.add_column("Attribute")
                    attr_table.add_column("Count")
                    attr_table.add_column("Tags Using It")

                    for attr, stats in sorted(
                        attr_stats.items(), key=lambda x: x[1]["count"], reverse=True
                    ):
                        attr_table.add_row(
                            f"[bold]{attr}[/]",
                            str(stats["count"]),
                            ", ".join(sorted(stats["tags"])),
                        )

                    console.print("\n[bold cyan]Attribute Usage Summary:[/]")
                    console.print(attr_table)

                    # Show detailed results tree
                    results_tree = Tree("[bold cyan]🏷️ Elements with Attributes[/]")
                    for item in result:
                        tag_node = results_tree.add(f"[bold]{item['tag']}[/]")
                        for attr, value in item["attributes"].items():
                            tag_node.add(f"[green]{attr}[/]: {value}")
                        if item["text"]:
                            preview = (
                                item["text"][:50] + "..."
                                if len(item["text"]) > 50
                                else item["text"]
                            )
                            tag_node.add(f"[yellow]Text: {preview}[/]")

                    console.print("\n[bold cyan]Detailed Element Analysis:[/]")
                    console.print(results_tree)
                else:
                    console.print(
                        "\n[bold yellow]! No elements with attributes found[/]"
                    )

                # Complete progress
                progress.update(attr_task, advance=30)

            console.print("\n[bold green]✓ Attribute extraction complete![/]")

        elif action == "modify":
            # modifications is now a direct parameter
            if not modifications:
                raise ValueError("No modifications specified")

            changes_made = []

            # Create a progress bar for modifications
            with Progress() as progress:
                modify_task = progress.add_task(
                    "[green]Processing modifications...", total=len(modifications)
                )
                console.print(Panel.fit("Starting HTML modifications", style="blue"))

            for mod in modifications:
                if not mod.get("target"):
                    raise ValueError("Target selector is required for modification")

                try:
                    elements = soup.select(mod["target"])
                    if not elements:
                        changes_made.append(
                            f"Warning: No elements found for selector '{mod['target']}'"
                        )
                        continue

                    action_type = mod["action"]
                    content_required = action_type in ["insert", "append", "replace"]

                    if content_required and not mod.get("content"):
                        raise ValueError(
                            f"Content is required for {action_type} action"
                        )

                    for element in elements:
                        try:
                            if action_type == "insert":
                                new_tag = BeautifulSoup(mod["content"], parser).find()
                                if new_tag:
                                    element.insert_before(new_tag)
                                    changes_made.append(
                                        f"Inserted content before {mod['target']}"
                                    )
                                else:
                                    changes_made.append(
                                        f"Warning: Invalid content for insertion at {mod['target']}"
                                    )

                            elif action_type == "append":
                                new_content = BeautifulSoup(mod["content"], parser)
                                element.append(new_content)
                                changes_made.append(
                                    f"Appended content to {mod['target']}"
                                )

                            elif action_type == "replace":
                                new_content = BeautifulSoup(
                                    mod["content"], parser
                                ).find()
                                if new_content:
                                    element.replace_with(new_content)
                                    changes_made.append(f"Replaced {mod['target']}")
                                else:
                                    changes_made.append(
                                        f"Warning: Invalid content for replacement at {mod['target']}"
                                    )

                            elif action_type == "clear":
                                element.clear()
                                changes_made.append(
                                    f"Cleared contents of {mod['target']}"
                                )

                            elif action_type == "unwrap":
                                element.unwrap()
                                changes_made.append(f"Unwrapped {mod['target']}")

                            progress.update(modify_task, advance=1)
                            console.print(
                                f"✓ Completed: {action_type} on {mod['target']}",
                                style="green",
                            )

                        except Exception as elem_error:
                            changes_made.append(
                                f"Error modifying element {mod['target']}: {str(elem_error)}"
                            )

                except Exception as selector_error:
                    changes_made.append(
                        f"Invalid selector '{mod['target']}': {str(selector_error)}"
                    )

            # Create a summary table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Action")
            table.add_column("Target")
            table.add_column("Status")

            for change in changes_made:
                if ":" in change:
                    action, detail = change.split(":", 1)
                    table.add_row(
                        action.strip(),
                        detail.strip(),
                        "✓" if "Error" not in change else "✗",
                        style="green" if "Error" not in change else "red",
                    )

            console.print("\nModification Summary:")
            console.print(table)

            result = {
                "modified_html": str(soup),
                "changes": changes_made,
                "status": "complete" if changes_made else "no_changes",
            }

        elif action == "navigate":
            console.print(
                Panel.fit("[bold blue]Navigating Document Structure", style="blue")
            )
            # navigation is now a direct parameter
            direction = navigation.get("direction", "children")

            with Progress() as progress:
                nav_task = progress.add_task(
                    "[green]Analyzing document structure...", total=100
                )

                # Initialize navigation
                progress.update(nav_task, advance=20)
                start_element = soup.find() if direction != "parent" else soup

                # Create direction info panel
                direction_info = Panel.fit(
                    (
                        f"[bold]Direction:[/] {direction}\n"
                        f"[bold]Starting from:[/] {start_element.name if start_element else 'root'}"
                    ),
                    title="Navigation Parameters",
                    style="cyan",
                )
                console.print("\n")
                console.print(direction_info)

                # Navigate and collect elements
                progress.update(nav_task, advance=30)
                if direction == "parent":
                    elements = [start_element.parent] if start_element.parent else []
                elif direction == "children":
                    elements = list(
                        filter(lambda x: isinstance(x, Tag), start_element.children)
                    )
                elif direction == "siblings":
                    elements = list(
                        filter(
                            lambda x: isinstance(x, Tag),
                            list(start_element.next_siblings)
                            + list(start_element.previous_siblings),
                        )
                    )
                elif direction == "descendants":
                    elements = list(
                        filter(lambda x: isinstance(x, Tag), start_element.descendants)
                    )
                elif direction == "ancestors":
                    elements = list(
                        filter(lambda x: isinstance(x, Tag), start_element.parents)
                    )

                # Process elements
                progress.update(nav_task, advance=30)
                result = [extract_element_data(el) for el in elements if el]

                # Create visual representation
                if result:
                    # Create element tree
                    nav_tree = Tree(
                        f"[bold cyan]🌐 {direction.title()} of {start_element.name}[/]"
                    )

                    for idx, element in enumerate(elements, 1):
                        if isinstance(element, Tag):
                            # Create node label
                            classes = element.get("class", [])
                            class_str = f" .{'.'.join(classes)}" if classes else ""
                            id_str = f" #{element['id']}" if element.get("id") else ""

                            # Add text preview if available
                            text = clean_text(element.string)
                            text_preview = (
                                f": {text[:30]}..."
                                if text and len(text) > 30
                                else f": {text}" if text else ""
                            )

                            node_label = (
                                f"{element.name}{class_str}{id_str}{text_preview}"
                            )
                            element_node = nav_tree.add(f"[bold]{idx}.[/] {node_label}")

                            # Add attribute information
                            if element.attrs:
                                attrs_node = element_node.add("[yellow]Attributes[/]")
                                for attr, value in element.attrs.items():
                                    attrs_node.add(f"[green]{attr}[/]: {value}")

                    console.print("\n[bold cyan]Navigation Results:[/]")
                    console.print(nav_tree)

                    # Create statistics table
                    stats_table = Table(show_header=True, header_style="bold magenta")
                    stats_table.add_column("Statistic")
                    stats_table.add_column("Value")

                    tag_counts = {}
                    total_attrs = 0
                    total_text_length = 0

                    for el in elements:
                        if isinstance(el, Tag):
                            tag_counts[el.name] = tag_counts.get(el.name, 0) + 1
                            total_attrs += len(el.attrs)
                            total_text_length += len(clean_text(el.text))

                    stats_table.add_row("Total Elements", str(len(elements)))
                    stats_table.add_row("Unique Tags", str(len(tag_counts)))
                    stats_table.add_row("Total Attributes", str(total_attrs))
                    stats_table.add_row("Total Text Length", str(total_text_length))

                    console.print("\n[bold cyan]Element Statistics:[/]")
                    console.print(stats_table)
                else:
                    console.print(
                        "\n[bold yellow]! No elements found in specified direction[/]"
                    )

                # Complete progress
                progress.update(nav_task, advance=20)

            console.print("\n[bold green]✓ Navigation complete![/]")

        return {
            "status": "success",
            "content": [
                {"text": f"Action '{action}' completed successfully"},
                {"text": f"Results: {json.dumps(result, indent=2)}"},
            ],
        }

    except Exception as e:
        return {
            "status": "error",
            "content": [{"text": f"Error: {str(e)}"}],
        }
