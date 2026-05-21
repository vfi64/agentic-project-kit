from pathlib import Path


ROADMAP = Path("docs/strategy/V0.4.0_GUI_MVP_ROADMAP.md")


def test_v040_gui_mvp_roadmap_exists():
    assert ROADMAP.exists()


def test_v040_gui_mvp_roadmap_defines_phase_boundary():
    text = ROADMAP.read_text(encoding="utf-8")
    assert "v0.3.37 closes the pre-GUI hardening phase" in text
    assert "No further general pre-GUI 0.3.x preparation loop is planned" in text
    assert "Remaining test gaps are handled as entry conditions inside the first v0.4.0 GUI slices" in text


def test_v040_gui_mvp_roadmap_locks_safety_principles():
    text = ROADMAP.read_text(encoding="utf-8")
    assert "The GUI uses the existing action registry and action specs" in text
    assert "The GUI uses the existing mode guard" in text
    assert "The GUI must preserve evidence and terminal-log discipline" in text
    assert "The GUI must not reintroduce removed shell adapters" in text


def test_v040_gui_mvp_roadmap_blocks_destructive_mvp_actions():
    text = ROADMAP.read_text(encoding="utf-8")
    assert "Destructive actions are disabled in the first GUI MVP" in text
    assert "Release, publish, merge, tag, delete, and remote-mutating actions are not directly executable" in text
    assert "Any future destructive GUI action requires a separate contract" in text


def test_v040_gui_mvp_roadmap_orders_first_slices():
    text = ROADMAP.read_text(encoding="utf-8")
    expected = [
        "1. Strategy and roadmap update",
        "2. GUI action readiness contract",
        "3. GUI dry-run entry point",
        "4. Minimal Tkinter MVP",
        "5. GUI help baseline",
    ]
    positions = [text.index(item) for item in expected]
    assert positions == sorted(positions)



def test_v040_gui_mvp_roadmap_has_document_lifecycle_header():
    text = ROADMAP.read_text(encoding="utf-8")
    assert "Status: proposed" in text
    assert "Decision status: proposed" in text
    assert "Status: planned first" not in text
    assert "Planning note: first v0.4.0 line after v0.3.37 release and DOI closeout." in text
