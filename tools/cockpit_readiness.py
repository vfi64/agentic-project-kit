from agentic_project_kit.cockpit_readiness import render_cockpit_readiness_markdown


def main() -> int:
    print(render_cockpit_readiness_markdown(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
