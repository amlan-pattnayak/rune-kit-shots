#!/usr/bin/env python3
"""Merges the hand-written catalog with api.json, stories.json and the shots manifest into
site/data.json.   usage: build_site.py <data dir> <shots dir> <site dir>"""
import json
import re
import sys
from pathlib import Path

DATA, SHOTS, SITE = (Path(p) for p in sys.argv[1:4])
REV = "0c8a62e777b171f41cd0c99fb66c63d1b386e899"

# (slug, name, group, summary, types, scene-id prefixes, feature)
C = [
 ("button", "Button", "Actions", "A text button in ten variants and five control sizes, with an optional icon, a loading look and a label that can roll its changed characters.", ["Button", "ButtonVariant", "ButtonSize"], ["ui-button--"], None),
 ("icon-button", "IconButton", "Actions", "A square, icon-only button. Give it a label or help text so screen readers can name it.", ["IconButton", "IconButtonVariant"], ["ui-icon-button--"], None),
 ("switch", "Switch", "Selection", "An on/off toggle with a label and description, in compact, standard and web looks and five control sizes.", ["Switch"], ["ui-switch--", "rune-switch--"], None),
 ("checkbox", "Checkbox", "Selection", "A checkbox with a label, a description, an indeterminate state and a custom check icon.", ["Checkbox"], ["ui-checkbox--"], None),
 ("radio", "RadioGroup", "Selection", "A labelled group of radio items. Arrow keys move between items.", ["RadioGroup", "RadioItem"], ["ui-radio--"], None),
 ("segmented-control", "SegmentedControl", "Selection", "A row of segments where one is picked, sized to a width or to its labels.", ["SegmentedControl"], ["ui-segmented-control--"], None),
 ("text-input", "TextInput", "Text entry", "A single-line field with a placeholder, leading icon, copy and clear buttons, secure entry, an invalid state and key interception. TextField is the older labelled field.", ["TextInput", "TextField"], ["ui-text-input--"], None),
 ("text-area", "TextArea", "Text entry", "A multi-line field with fixed rows or auto-grow between a minimum and maximum.", ["TextArea"], ["ui-textarea--"], None),
 ("rich-editor", "Rich text editing", "Text entry", "TextInput, TextArea and TextField accept decorations, a rich style and mention pills. This is the rich_editor example from the kit.", [], ["example-rich_editor"], None),
 ("field", "Field", "Text entry", "Wraps a control with a label, an info mark, and prefix and suffix text.", ["Field"], ["ui-field--"], None),
 ("select", "Select", "Text entry", "A dropdown of options, flat or grouped, with an inline or field-style trigger. Its list is an overlay.", ["Select", "SelectAppearance"], ["ui-select--", "rune-select--"], None),
 ("combobox", "Combobox", "Text entry", "A searchable select built from Popover, TextInput and virtual rows. It filters as you type and only lays out mounted rows.", ["Combobox", "ComboboxOption", "ComboboxState", "ComboboxEvent", "ComboboxPhase", "ComboboxEffect"], ["rune-combobox--"], None),
 ("shortcut-recorder", "ShortcutRecorder", "Text entry", "Click to record a keyboard shortcut. Escape cancels, Backspace clears, and a refused chord shows an error.", ["ShortcutRecorder", "ShortcutRecorderState", "shortcut_error_message"], ["example-shortcut_recorder"], None),
 ("popover", "Popover", "Overlays", "Titled content anchored to a trigger. It flips and shifts to stay inside the window.", ["Popover", "Placement", "body_text", "overlay_text", "scrim"], ["components-popover--"], None),
 ("menu", "Menu", "Overlays", "A dropdown menu with icons, shortcuts, badges, descriptions, checkbox and radio items, submenus and a context-menu form.", ["Menu", "MenuItem", "MenuEntry", "context_menu"], ["ui-menu--"], None),
 ("tooltip", "Tooltip", "Overlays", "A tooltip in compact, standard and large looks, with keybind hints and a title-and-description form.", ["Tooltip", "TooltipAppearance", "TooltipStyle"], ["ui-tooltip--", "rune-text--selectable-help"], None),
 ("hover-card", "HoverCard", "Overlays", "A rich preview anchored under its trigger, shown on hover.", ["HoverCard"], ["components-hover-card--"], None),
 ("dialog", "Dialog", "Overlays", "A modal dialog over a scrim. It traps focus and returns it to the opener on close.", ["Dialog"], ["ui-dialog--", "rune-dialog--", "motion-focus-modal"], None),
 ("toast", "Toast", "Overlays", "A notification with an icon, description and actions. ToastRegion stacks them at the bottom right; ToastStack is the state machine for timers and stacking.", ["Toast", "ToastRegion", "ToastStack", "ToastEntry", "ToastTimer", "ToastStackState", "ToastEvent", "ToastEffect", "ToastPlacement"], ["ui-toast--"], None),
 ("popup-list", "PopupList", "Overlays", "A popup listbox driven by a field elsewhere, for @-mentions and /-commands. Keyboard focus stays in the field.", ["PopupList", "PopupItem"], ["rune-popup-list--"], None),
 ("card", "Card", "Display", "A bordered block with a title, description and action, in normal, error, warning, success and info accents.", ["Card"], ["components-card--"], None),
 ("list", "List", "Display", "A selectable list with groups, search, dividers, an active icon, an add row and an empty message.", ["List", "ListItem"], ["components-list--", "motion-stagger-list"], None),
 ("accordion", "Accordion", "Display", "Stacked sections that expand and collapse, one or several at a time.", ["Accordion", "AccordionItem"], ["ui-accordion--"], None),
 ("collapsible", "Collapsible", "Display", "One disclosure: a trigger row that shows or hides its content.", ["Collapsible"], ["components-collapsible--"], None),
 ("badge", "Badge", "Display", "A small status label in neutral, accent and subtle variants. Divider, a one-point rule, lives beside it.", ["Badge", "BadgeVariant", "Divider"], ["ui-badge--"], None),
 ("keybind", "Keybind", "Display", "Keycaps for a shortcut, with platform symbols.", ["Keybind", "KeybindVariant"], ["ui-keybind--", "rune-keybind--"], None),
 ("rolling-text", "RollingText", "Display", "A label that rolls only the characters that changed.", ["RollingText"], ["rune-rolling-text--"], None),
 ("text", "Text helpers", "Display", "Core Rune text features the kit themes: selectable text with the kit's selection colour, and middle truncation.", [], ["rune-text--truncate-middle"], None),
 ("spinner", "Spinner", "Feedback", "The activity spinner: a five-by-five dot grid with a head that sweeps round each ring.", ["Spinner"], ["components-spinner--"], None),
 ("loader", "Loader", "Feedback", "A turning ring for loading that is not agent activity.", ["Loader"], ["ui-loader--"], None),
 ("progress", "Progress", "Feedback", "A linear bar with an optional label and value. ProgressCircle is a small ring that fills clockwise.", ["Progress", "ProgressCircle"], ["components-progress--"], None),
 ("scroll-bar", "ScrollBar", "Feedback", "The kit's scroll bar thumb styles for scrolling viewports.", ["ScrollBar", "ScrollBarStyle", "scroll_bar"], ["rune-scroll-bar--", "rune-scroll-view--"], None),
 ("table", "Table", "Data", "A virtualised table with sortable, resizable columns, selection and a keyboard cursor.", ["Table", "TableColumn", "Cell", "TableState", "TableStyle", "SortDir"], ["example-table"], None),
 ("tree", "Tree", "Data", "A virtualised tree. FileTree builds one from file paths, with natural sorting and compact folder chains.", ["Tree", "TreeItem", "TreeStyle", "FileTree", "FileNode", "TreeModel", "TreeRow", "TreeKey", "file_icon", "natural_cmp"], ["rune-tree--", "example-tree"], None),
 ("diff", "DiffView", "Data", "A code diff in unified or split layout with syntax highlighting, folding, line selection and annotations.", ["DiffView", "DiffState", "DiffMode", "FileDiff", "FileStatus", "Annotation", "LineRef", "LineRange", "Expand"], ["example-diff"], None),
 ("icons", "Icons and glyphs", "Data", "The kit's built-in glyphs, the OpenCode theme's icon catalog and the file-type icons the tree uses.", ["Glyphs"], ["ui-icon--", "rune-icon--", "components-file-icon--", "rune-file-icon--", "rune-tree-icon--", "example-glyphs"], None),
 ("markdown", "Markdown", "Content", "Renders Markdown, including streaming text, tables, code blocks with syntax highlighting, find highlights and selection.", ["Markdown", "MarkdownStyle", "Highlight", "Case", "ImageFrame", "CodeFrame", "QuoteFrame", "DiagramFrame", "Highlighter", "SyntaxTheme", "Syntax"], ["rune-markdown--basic", "rune-markdown--streaming", "rune-markdown--stream-tail", "rune-markdown--walkthrough", "rune-markdown--lenient", "rune-markdown--table-styles", "rune-markdown--code"], "markdown"),
 ("mermaid", "Mermaid diagrams", "Content", "Mermaid fences in Markdown draw as native diagrams.", [], ["rune-markdown--diagrams", "rune-markdown--mermaid-"], "mermaid"),
 ("note", "Note", "Content", "Markdown with structured blocks layered on top: facts, compare, steps and size blocks, titled or marked code fences, and callouts. Plain Markdown passes straight through. The gallery has no scene for it yet.", ["Note"], [], "markdown"),
 ("image-zoom", "ImageZoom", "Content", "A full-window image preview with zoom, pan and a zoom bar. Stage is the in-pane version. The gallery has no scene for it yet.", ["ImageZoom", "Preview", "Stage", "StageZoom"], [], None),
 ("split-view", "SplitView and Sidebar", "App shell", "The app shell: a sidebar, a main card, an inspector and a toolbar. Page is a full-window screen without side panes.", ["SplitView", "Sidebar", "SidebarSection", "SidebarRow", "SidebarHeader", "SidebarToggle", "SidebarPeek", "PaneState", "PaneMotion", "Toolbar", "Page", "Reorder"], ["example-shell"], None),
 ("tab-strip", "TabStrip", "App shell", "A strip of tabs that shrink, scroll, reorder by drag and tear out into windows. WindowTitlebar places one in the title bar.", ["TabStrip", "TabItem", "TabOrientation", "TabDensity", "TabOverflow", "TabItemStatus", "TabDragState", "WindowTitlebar"], ["example-tab_strip"], None),
 ("kit", "Kit and theming", "Foundations", "Every component reads its colours, type, radii, motion and glyphs from a Kit. Use a theme crate, Kit::neutral, or derive one from three colours with Kit::from_palette.", ["Kit", "PaletteSeed", "PaletteFocus", "Palette", "Elevation", "Type", "Radius", "Motion", "StateColors", "State", "ControlSize", "root"], [], None),
]


# Motion pages: (slug, name, summary, clip group, source path in the Rune repo)
M = [
 ("showreel", "Showreel scenes", "The purpose-made scenes behind the video in Rune's README. Each animates itself from the clock, so a headless run records it frame-exact.", "showreel", "examples/showreel"),
 ("effects-lab", "Effects lab", "rune-light and rune-fx composited live inside Rune's renderer: lights, glow, pulses, electricity, fire and a lens. Some clips replay a scripted pointer.", "lab", "examples/lab"),
 ("example-apps", "Example apps", "Scripted runs of example apps from the repo: the settings window, a matched-geometry zoom, and the twelve-tile motion bento.", "apps", "examples"),
]
# Scripted kit clips shown on their component's page.
KIT_CLIPS = {"kit-combobox": "combobox", "kit-combobox-animated-filter": "combobox", "kit-help-tooltip": "tooltip",
             "kit-selectable-text": "text", "kit-motion-focus-modal": "dialog", "kit-motion-stagger-list": "list"}


def clip(m):
    name = m["id"].split("-", 1)[1].replace("-", " ")
    return {"id": m["id"], "title": name[:1].upper() + name[1:], "file": m["file"], "w": m["w"], "h": m["h"],
            "dur": m["dur"], "cmd": m.get("cmd", "")}


def title(sid):
    tail = sid.split("--", 1)[1] if "--" in sid else sid
    t = tail.replace("-", " ").replace("_", " ")
    return t[:1].upper() + t[1:]


def main():
    api = json.loads((DATA / "api.json").read_text())
    stories = json.loads((DATA / "stories.json").read_text())
    manifest = json.loads((SHOTS / "manifest.json").read_text()) if (SHOTS / "manifest.json").exists() else []
    types = {}
    # On a name collision the crate-root or own-module definition wins over a private one.
    rank = lambda f: (f != "lib.rs", f.count("/"), f == "markdown.rs", f)
    for f in sorted(api, key=rank):
        for t in api[f]:
            if t["name"] in types:
                print("collision:", t["name"], "kept", types[t["name"]]["file"], "over", f)
            types.setdefault(t["name"], {**t, "file": f})
    shots = {}
    for m in manifest:
        if "error" in m:
            continue
        kit = "neutral" if m["kit"] == "neutral" else "opencode"
        shots.setdefault(m["id"], {}).setdefault(kit, {})[m["theme"]] = [m["file"], m["w"], m["h"]]
    cm = json.loads((SITE / "clips/manifest.json").read_text()) if (SITE / "clips/manifest.json").exists() else []
    bad = [m["id"] for m in cm if "error" in m]
    if bad:
        print("clips that failed:", bad)
    cm = [m for m in cm if "error" not in m]
    order = list(stories) + sorted(s for s in shots if s.startswith("example-"))
    used, comps = set(), []
    for slug, name, group, summary, tnames, prefixes, feature in C:
        ids = [s for s in order if any(s.startswith(p) for p in prefixes)]
        if slug == "markdown":
            ids = [s for s in ids if "mermaid" not in s and "diagrams" not in s]
        used.update(ids)
        scenes = []
        for s in ids:
            st = stories.get(s)
            scenes.append({"id": s, "title": title(s), "src": st["src"] if st else None,
                           "example": s.startswith("example-"), "shots": shots.get(s, {})})
        clips = [clip(m) for m in cm if KIT_CLIPS.get(m["id"]) == slug]
        comps.append({"slug": slug, "name": name, "group": group, "summary": summary, "feature": feature, "clips": clips,
                      "types": [types[t] for t in tnames if t in types], "scenes": scenes})
        miss = [t for t in tnames if t not in types]
        if miss:
            print("missing types", slug, miss)
    print("unassigned scenes:", [s for s in order if s not in used])
    print("scenes without shots:", [s["id"] for c in comps for s in c["scenes"] if not s["shots"]])
    motion = [{"slug": slug, "name": name, "group": "Motion", "summary": summary, "feature": None, "types": [], "scenes": [],
               "src": src, "clips": [clip(m) for m in cm if m["group"] == g]} for slug, name, summary, g, src in M]
    motion = [m for m in motion if m["clips"]]
    reel = next((clip(m) for m in cm if m["id"] == "rune-reel"), None)
    out = {"rev": REV, "reel": reel, "components": motion + comps}
    (SITE / "data.json").write_text(json.dumps(out, separators=(",", ":")))
    print(len(comps), "components,", sum(len(c["scenes"]) for c in comps), "scenes,", (SITE / "data.json").stat().st_size // 1024, "KB")


main()
