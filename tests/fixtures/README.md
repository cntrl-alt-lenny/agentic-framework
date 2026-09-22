# Test fixtures

`v2_adopter/` is a miniature project in the shape the three real adopters had
under release 2.x: unedited framework copies (taken byte-for-byte from release
2.1.0), an edited copy, a rendered neutrality test, project-local documents in
`docs/agents/`, an edited `.claude/settings.json` that still wires the retired
report hook, and a project pre-push hook that calls a retired tool.
`tests/test_adopt.py` migrates it to the current release and checks that
nothing project-owned or edited is lost.
