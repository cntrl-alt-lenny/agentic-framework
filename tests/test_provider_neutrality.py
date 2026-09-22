"""Lane identity must derive from roles, never from a provider.

Every rule here is a POSITIVE invariant over the declared role vocabulary, and
fails closed on anything unrecognised. No detector knows a provider name. The
proof is `TestNovelProviderIsRejected`, which uses a name appearing nowhere else
in this repository: if the guard only worked by recognising today's providers,
that name would sail through.

Historical documents are out of scope by design, and the scope split is itself
tested — a policy file cannot be exempted by adding it to a list.
"""

from __future__ import annotations

import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import docset  # noqa: E402
import neutrality  # noqa: E402
import textblocks  # noqa: E402

#: Declared once, in tools/docset.py, and imported everywhere else.
ROLES = docset.ROLES
COORDINATOR = docset.COORDINATOR

#: A name that must appear nowhere else in this repository.
NOVEL = "NebulaAI"


class TestScopeSplitIsHonest(unittest.TestCase):
    def test_normative_set_is_not_empty(self):
        self.assertGreaterEqual(
            len(docset.normative_files()), 10,
            "fail closed: a guard that scanned nothing must not pass",
        )

    def test_readme_standard_is_scanned_as_normative(self):
        readme_standard = (ROOT / "standards" / "readme.md").resolve()
        normative = {path.resolve() for path in docset.normative_files()}
        references = {path.resolve() for path in docset.reference_files()}
        self.assertIn(
            readme_standard,
            normative,
            "the active README standard must be scanned by both guards",
        )
        self.assertNotIn(
            readme_standard,
            references,
            "an active standard must not be classified as reference material",
        )

    def test_normative_and_historical_are_disjoint(self):
        normative = {p.resolve() for p in docset.normative_files()}
        historical = {p.resolve() for p in docset.historical_files()}
        self.assertEqual(normative & historical, set())

    def test_every_historical_file_declares_itself_historical(self):
        # Prevents the exemption list being used to quietly exempt a policy
        # document: doing so would require writing the marker into it.
        for path in docset.historical_files():
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), f"stale exemption: {path}")
                self.assertIn(
                    docset.HISTORICAL_MARKER,
                    path.read_text(encoding="utf-8").lower(),
                    "a file exempted from the normative scans must say so in "
                    "its own text",
                )

    def test_every_document_is_classified(self):
        """No third category. A new document is normative by default.

        Escaping the scans requires adding a file to HISTORICAL *and* writing
        the marker into it, or declaring it a fixture — both visible acts.
        CHANGELOG.md was briefly in neither set, which is exactly the hole this
        closes.
        """
        stray = [p.relative_to(ROOT).as_posix() for p in docset.unclassified()]
        self.assertEqual(
            stray, [],
            f"unclassified documents (neither normative, historical, nor a "
            f"declared fixture): {stray}",
        )

    def test_new_framework_documents_are_scanned_by_default(self):
        scanned = {p.resolve() for p in docset.normative_files()}
        exempt = {p.resolve() for p in docset.historical_files()}
        for path in docset.tracked_markdown_files():
            if ROOT / "framework" not in path.parents:
                continue
            with self.subTest(path=path.name):
                self.assertIn(path.resolve(), scanned | exempt)


class TestNormativeSurfaceIsRoleBased(unittest.TestCase):
    def _scan(self, path: Path) -> neutrality.ScanResult:
        return neutrality.scan(
            path.read_text(encoding="utf-8"), ROLES,
            source=path.relative_to(ROOT).as_posix(), coordinator=COORDINATOR,
        )

    def test_declared_role_branch_placeholder_is_not_a_provider_namespace(self):
        for text in (
            "Push your work on builder/<scope> and open a pull request.",
            "Push your work on `builder/<scope>` and open a pull request.",
            "Push your work on builder/feature-42 and open a pull request.",
            "Push your work on `builder/feature-42` and open a pull request.",
        ):
            with self.subTest(text=text):
                self.assertEqual(neutrality.scan(text, ROLES).findings, [])

    def test_declared_structural_branch_namespaces_are_allowed(self):
        text = (
            "Create branch `m3/feature-work` for the next milestone.\n"
            "Keep branch namespace `meta/coordination` for project structure.\n"
        )
        self.assertEqual(
            neutrality.scan(
                text, ("builder", "verifier"),
                branch_namespaces=("m<N>", "meta"),
            ).findings,
            [],
        )

    def test_declared_custom_namespace_is_a_reviewed_boundary(self):
        """Evidence and declaration are checked; provider identity is not."""
        result = neutrality.scan(
            "Create branch `codex/next` for this project.\n",
            ("builder", "verifier"),
            branch_namespaces=("codex",),
        )
        self.assertEqual(result.findings, [])

    def test_hyphenated_project_namespace_needs_a_real_witness(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
            (root / "docs" / "branch-namespaces").mkdir(parents=True)
            (root / "docs" / "branch-namespaces" / "modern-ui.md").write_text(
                "The legacy web application owns modern-ui branches for UI work; "
                "it is not a role or provider lane.\n",
                encoding="utf-8",
            )
            (root / "AGENTS.md").write_text(
                '<!-- guard:branch-namespaces prefixes="modern-ui" -->\n',
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "witness"], cwd=root, check=True)
            self.assertEqual(
                neutrality.branch_namespace_declarations(
                    (root / "AGENTS.md").read_text(), root=root,
                    roles=("builder",),
                ),
                ("modern-ui",),
            )
            self.assertEqual(
                neutrality.scan(
                    "Create branch `modern-ui/next` for the legacy UI.\n",
                    ("builder",), branch_namespaces=("modern-ui",),
                ).findings,
                [],
            )

            (root / "docs" / "branch-namespaces" / "acme-builder.md").write_text(
                "The project owns this branch namespace.\n", encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "role witness"], cwd=root, check=True)
            with self.assertRaisesRegex(ValueError, "declared role"):
                neutrality.branch_namespace_declarations(
                    '<!-- guard:branch-namespaces prefixes="acme-builder" -->',
                    root=root, roles=("builder",),
                )

    def test_hyphenated_declared_roles_and_coordinator_are_refused_everywhere(self):
        roles = ("lead-brain", "build-team")
        coordinator = "chief-coordinator"
        for namespace in (
            "acme-lead-brain", "acme-build-team", "acme-chief-coordinator",
        ):
            with self.subTest(namespace=namespace):
                declaration = (
                    f'<!-- guard:branch-namespaces prefixes="{namespace}" -->'
                )
                with self.assertRaisesRegex(ValueError, "declared role"):
                    neutrality.branch_namespace_declarations(
                        declaration, roles=roles, coordinator=coordinator,
                    )
                with self.assertRaisesRegex(ValueError, "declared role"):
                    neutrality.scan(
                        f"Create branch `{namespace}/next` for this round.\n",
                        roles, coordinator=coordinator,
                        branch_namespaces=(namespace,),
                    )

    def test_command_line_uses_the_same_hyphenated_role_context(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
            (root / "docs" / "branch-namespaces").mkdir(parents=True)
            (root / "docs" / "branch-namespaces" / "acme-lead-brain.md").write_text(
                "This is established project structure, not a role or provider lane.\n",
                encoding="utf-8",
            )
            (root / "AGENTS.md").write_text(
                '<!-- guard:branch-namespaces prefixes="acme-lead-brain" -->\n'
                "Create branch `acme-lead-brain/next` for this round.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "witness"], cwd=root, check=True)
            proc = subprocess.run(
                [
                    sys.executable, str(ROOT / "tools" / "neutrality.py"),
                    str(root / "AGENTS.md"), "--roles", "lead-brain,build-team",
                    "--coordinator", "chief-coordinator",
                ],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("declared role", proc.stdout + proc.stderr)

    def test_installed_guard_passes_rendered_role_context_to_declaration_discovery(self):
        template = (ROOT / "templates" / "tests" / "test_role_neutrality.py").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "branch_namespaces_for_paths(\n"
            "        [str(ROOT)], roles=ROLES, coordinator=COORDINATOR\n"
            "    )",
            template,
        )

    def test_namespace_boundary_is_documented_without_a_vendor_claim(self):
        for path in (
            ROOT / "framework" / "CONSTITUTION.md",
            ROOT / "framework" / "adoption.md",
            ROOT / "templates" / "AGENTS.md",
        ):
            text = path.read_text(encoding="utf-8").lower()
            with self.subTest(path=path):
                self.assertIn("does not identify providers", text)
                self.assertIn("reviewed human", text)
        template = (ROOT / "templates" / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("single hyphens", template)
        self.assertIn("hyphenated role", template)
        self.assertIn("filename-only formality", template)
        adoption = (ROOT / "framework" / "adoption.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("vendor-ai` is rejected", adoption)

    def test_undeclared_or_unbounded_branch_namespaces_still_fail(self):
        text = "Create `vendor/release` as a branch namespace.\n"
        self.assertTrue(
            any(
                finding.rule == "branch-namespace"
                for finding in neutrality.scan(
                    text, ("builder", "verifier"),
                    branch_namespaces=("m<N>", "meta"),
                ).findings
            )
        )
        self.assertEqual(
            neutrality.branch_namespace_declarations(
                '<!-- guard:branch-namespaces prefixes="release,feature" -->'
            ),
            ("release", "feature"),
        )
        self.assertEqual(
            neutrality.branch_namespace_declarations(
                '<!-- guard:branch-namespaces prefixes="m<N>,vendor-ai" -->'
            ),
            ("m<N>", "vendor-ai"),
        )
        with self.assertRaisesRegex(ValueError, "tracked project-structure"):
            neutrality.branch_namespace_declarations(
                '<!-- guard:branch-namespaces prefixes="m<N>,vendor-ai" -->',
                root=ROOT,
            )
        with self.assertRaisesRegex(ValueError, "tracked project-structure"):
            neutrality.branch_namespace_declarations(
                '<!-- guard:branch-namespaces prefixes="vendor" -->',
                root=ROOT,
            )
        self.assertEqual(
            neutrality.branch_namespace_declarations(
                '```text\n<!-- guard:branch-namespaces prefixes="m<N>,meta" -->\n```'
            ),
            (),
        )

    def test_branch_namespace_declarations_ignore_markdown_and_html_examples(self):
        for example in (
            '```markdown\n<!-- guard:branch-namespaces prefixes="release" -->\n```',
            '~~~markdown\n<!-- guard:branch-namespaces prefixes="release" -->\n~~~',
            '````markdown\n'
            '```\n<!-- guard:branch-namespaces prefixes="release" -->\n```\n'
            '````',
            '    <!-- guard:branch-namespaces prefixes="release" -->',
            '<pre>\n<!-- guard:branch-namespaces prefixes="release" -->\n</pre>',
            '<code>\n<!-- guard:branch-namespaces prefixes="release" -->\n</code>',
            '<textarea>\n<!-- guard:branch-namespaces prefixes="release" -->\n</textarea>',
            '<script>\n<!-- guard:branch-namespaces prefixes="release" -->\n</script>',
            '<style>\n<!-- guard:branch-namespaces prefixes="release" -->\n</style>',
        ):
            with self.subTest(example=example):
                self.assertEqual(
                    neutrality.branch_namespace_declarations(example), ()
                )

    def test_capitalised_roles_in_adjacent_sentences_are_not_one_lane(self):
        for text in (
            "Hand the report to the Verifier. That Builder then waits.",
            "The Builder finished. Verifier reviews the exact commit.",
            "A Worker stops here! The Verifier continues independently.",
        ):
            with self.subTest(text=text):
                self.assertEqual(neutrality.scan(text, ROLES).findings, [])

    def test_dotted_qualifiers_before_roles_are_rejected(self):
        cases = (
            "Hand the brief to the Mosaic.io Builder.",
            "Route the result to the Rho7.4 Verifier after review.",
            "The North Star.dev Researcher owns the evidence note.",
            "Use the Ember2.0 Scaffolder for this setup step.",
            "A Quartz.site Worker wrote the first draft.",
        )
        for text in cases:
            with self.subTest(text=text):
                findings = neutrality.scan(text, ROLES).findings
                self.assertTrue(
                    any(f.rule == "compound-lane" for f in findings),
                    f"dotted provider-shaped qualifier was not rejected: {text}",
                )

    def test_capitalised_hyphenated_compounds_before_roles_are_clean(self):
        cases = (
            "Self-contained Builder prompts are short.",
            "The Follow-up Builder brief is ready.",
            "Keep the Cross-team Verifier note nearby.",
            "A North-facing Worker checklist is useful.",
            "Use the Post-review Researcher summary.",
            "The High-level Scaffolder guidance is ordinary prose.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(neutrality.scan(text, ROLES).findings, [])

    def test_prefixed_lane_requires_identity_context_not_token_shape(self):
        clean = (
            "The deck-builder UI is separate.",
            "A world-builder tool is documented.",
            "See deck-builder-ui.md for details.",
            "See ../edopro-next-builder for details.",
            "The record-builder module is ordinary text.",
            "A self-builder pattern appears in the manual.",
            "The deck-builder module handles queue serialization.",
            "The deck-builder path is relative to the checkout.",
            "The release-builder file is mentioned beside the queue guide.",
            "A cross-team-builder example belongs in the UI manual.",
        )
        caught = (
            "The vendor-builder lane is isolated.",
            "Use the `vendor-builder` queue.",
            "The vendor-ai-builder lane is isolated.",
            "Use the `vendor-ai-builder` queue.",
            "Create vendor-builder/queue for this seat.",
            "The vendor-builder worktree is separate.",
            "Send the task to vendor-builder.",
            "Route the result through vendor-builder role.",
            "The queue is vendor-ai-builder for now.",
            "Create vendor-ai-builder/queue for this round.",
        )
        for text in clean:
            with self.subTest(text=text):
                self.assertEqual(neutrality.scan(text, ROLES).findings, [])
        for text in caught:
            with self.subTest(text=text):
                self.assertTrue(
                    any(
                        finding.rule == "prefixed-lane"
                        for finding in neutrality.scan(text, ROLES).findings
                    ),
                    text,
                )

    def test_no_provider_shaped_lane_identity(self):
        problems: list[str] = []
        for path in docset.normative_files():
            problems += [str(f) for f in self._scan(path).findings]
        self.assertEqual(problems, [], "\n".join(problems))

    def test_no_inert_counterexample_blocks_of_this_scanners_own(self):
        """Symmetric to authority.py's own check: this scanner must not
        claim a block belonging entirely to a DIFFERENT scanner (e.g.
        authority.py's `routine-approval`) is its own inert exemption. No
        real document currently triggers this direction -- see
        TestCounterexampleBlockOwnership for the synthetic proof that closes
        the general mechanism, not just the currently-observed direction.
        """
        problems: list[str] = []
        for path in docset.normative_files():
            problems += [
                f"{path.relative_to(ROOT).as_posix()}:{c.line} counterexample "
                f"block suppresses nothing"
                for c in self._scan(path).inert_counterexamples()
            ]
        self.assertEqual(problems, [], "\n".join(problems))

    def test_counterexample_blocks_do_not_hide_real_violations(self):
        """Suppression must be scoped to the marked block, nothing wider.

        Joint honesty of the blocks themselves — that each is rejected by at
        least one guard — is checked once in `test_guard_honesty.py`, because
        the marker is shared between guards and a block may exist for either.
        """
        import textblocks
        for path in docset.all_documents():
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            opens = text.count(textblocks.COUNTEREXAMPLE_OPEN)
            closes = text.count(textblocks.COUNTEREXAMPLE_CLOSE)
            with self.subTest(path=rel):
                # An unclosed block suppresses everything to end of file, which
                # would silently disable the guard for the rest of the document.
                self.assertEqual(
                    opens, closes,
                    "unbalanced counterexample markers: an unclosed block "
                    "suppresses the rest of the file",
                )

    def test_counterexample_probe_handles_an_unlisted_specialist_role(self):
        body = (
            '<!-- guard:violation compound-lane roles=decomper '
            'text="Claude Decomper" -->\n'
            "- `Claude Decomper` and `Codex Decomper` as two lanes — that is "
            "one Decomper, run twice.\n"
        )
        findings = neutrality.scan_counterexample(body, ("builder",))
        self.assertTrue(
            any(f.rule == "compound-lane" for f in findings),
            "a marked example must be checked even when it quotes an unlisted "
            "specialist role",
        )

    def test_counterexample_probe_still_leaves_harmless_text_inert(self):
        for body in (
            "Think of the follow-up as a queue of small tasks.\n",
            "Keep the pre-push hook as a branch guard.\n",
            "The e-mail list serves as a queue.\n",
            "Store long-term notes as a branch of the wiki.\n",
            "Treat well-known names as a role hint.\n",
            "This role illustrates role-based delegation.\n",
            "Each branch uses a well-known best-practice layout.\n",
            "The role of a long-term plan is explained here.\n",
            "A queue of ordinary tasks is drained overnight.\n",
            "Namespace collisions are documented in the glossary.\n",
            "The lane is a metaphor for sequence, not a standing seat.\n",
            "Use `well-known` names in prose.\n",
            "The queue records ordinary work items.\n",
            "A branch of the documentation tree is useful.\n",
            "Role-based access is described in the policy.\n",
            "The namespace is reserved for examples.\n",
            "The follow-up lane is a step in the process.\n",
            "A well-known queue name appears in a quotation.\n",
            "The long-term branch plan is archived.\n",
            "This role's scope is intentionally narrow.\n",
            "The pre-push branch guard is documented.\n",
            "A task lane marks sequence in the diagram.\n",
        ):
            with self.subTest(body=body):
                self.assertEqual(neutrality.scan_counterexample(
                    body, ("builder", "verifier")
                ), [])

    def test_counterexample_probe_catches_lane_syntax_beyond_declared_roles(self):
        for body, rule in (
            (
                '<!-- guard:violation compound-lane roles=builder '
                'text="Acme Builder" -->\n'
                "Hand it to the Acme Builder.\n",
                "compound-lane",
            ),
            (
                '<!-- guard:violation prefixed-lane roles=builder '
                'text="codex-builder" -->\n'
                "Use the `codex-builder` queue.\n",
                "prefixed-lane",
            ),
            (
                '<!-- guard:violation branch-namespace roles=builder '
                'text="acme/some-scope" -->\n'
                "Cut `acme/some-scope` for this branch.\n",
                "branch-namespace",
            ),
            (
                '<!-- guard:violation prefixed-lane roles=scaffolder '
                'text="codex-scaffolder" -->\n'
                "Use `codex-scaffolder` as a queue name.\n",
                "prefixed-lane",
            ),
        ):
            with self.subTest(body=body):
                findings = neutrality.scan_counterexample(
                    body, ("builder", "verifier")
                )
                self.assertTrue(
                    any(f.rule == rule for f in findings),
                    f"{body!r} was not reported as {rule}: {findings}",
                )

    def test_counterexample_declarations_cover_adversarial_real_violations(self):
        cases = (
            ("compound-lane", "builder", "Acme Builder", "Hand it to the Acme Builder."),
            ("prefixed-lane", "builder", "codex-builder", "Use the `codex-builder` queue."),
            ("branch-namespace", "builder", "acme/some-scope", "Cut `acme/some-scope` for this branch."),
            ("prefixed-lane", "scaffolder", "codex-scaffolder", "Send the task to `codex-scaffolder`."),
            ("prefixed-lane", "researcher", "gemini-researcher", "Use the `gemini-researcher` queue."),
            ("prefixed-lane", "researcher", "claude-researcher", "Route everything through the claude-researcher lane."),
            ("branch-namespace", "decomper", "claude-decomper/fix-123", "Cut `claude-decomper/fix-123` for this."),
            ("compound-lane", "scaffolder", "Acme Scaffolder", "Hand it to the Acme Scaffolder."),
            ("compound-lane", "reviewer", "Polaris Reviewer", "Send this to the Polaris Reviewer."),
            ("prefixed-lane", "worker", "orbit-worker", "Use the `orbit-worker` queue."),
            ("branch-namespace", "builder", "nova/release", "Create `nova/release` as a branch namespace."),
            ("compound-lane", "researcher", "Polaris Researcher", "Hand it to the Polaris Researcher."),
            ("compound-lane", "worker", "Delta Worker", "Route this to the Delta Worker."),
            ("compound-lane", "decomper", "Acme Decomper", "Assign the Acme Decomper."),
            ("prefixed-lane", "verifier", "nebula-verifier", "Use the `nebula-verifier` queue."),
            ("prefixed-lane", "researcher", "orion-researcher", "Route it through the `orion-researcher` lane."),
            ("prefixed-lane", "scaffolder", "atlas-scaffolder", "Send it to the `atlas-scaffolder` queue."),
            ("branch-namespace", "builder", "quasar-builder/issue-42", "Cut `quasar-builder/issue-42` for this."),
            ("branch-namespace", "researcher", "atlas-researcher/design", "Create `atlas-researcher/design` as a branch namespace."),
            ("prefixed-lane", "decomper", "lumen-decomper", "Use the `lumen-decomper` lane."),
            ("prefixed-lane", "verifier", "nova-verifier", "Send it to the `nova-verifier` queue."),
        )
        for rule, declared_roles, matched, body in cases:
            declaration = (
                f'<!-- guard:violation {rule} roles={declared_roles} '
                f'text="{matched}" -->\n{body}\n'
            )
            with self.subTest(matched=matched):
                findings = neutrality.scan_counterexample(
                    declaration, ("builder", "verifier")
                )
                self.assertTrue(
                    any(f.rule == rule for f in findings),
                    f"{matched!r} was not reported as {rule}: {findings}",
                )

    def test_counterexample_exempts_only_declared_rule_and_text(self):
        cases = (
            (
                "declared branch, undeclared branch and compound",
                '<!-- guard:counterexample -->\n'
                '<!-- guard:violation branch-namespace roles=builder '
                'text="acme/some-scope" -->\n'
                "Cut `acme/some-scope` for this branch.\n"
                "git checkout -b nebula/builder-task origin/master\n"
                "Hand this to the NebulaAI Builder.\n"
                "<!-- /guard:counterexample -->\n",
                {"branch-namespace", "compound-lane"},
            ),
            (
                "declared compound, undeclared prefixed lane",
                '<!-- guard:counterexample -->\n'
                '<!-- guard:violation compound-lane roles=builder '
                'text="Acme Builder" -->\n'
                "Hand it to the Acme Builder. Use the `nebula-builder` queue.\n"
                "<!-- /guard:counterexample -->\n",
                {"prefixed-lane"},
            ),
            (
                "declared prefixed lane, undeclared branch",
                '<!-- guard:counterexample -->\n'
                '<!-- guard:violation prefixed-lane roles=builder '
                'text="codex-builder" -->\n'
                "Use the `codex-builder` queue.\n"
                "Create branch `nebula/release` for this round.\n"
                "<!-- /guard:counterexample -->\n",
                {"branch-namespace"},
            ),
        )
        for name, text, rules in cases:
            with self.subTest(name=name):
                result = neutrality.scan(text, ("builder", "verifier"))
                self.assertTrue(result.findings)
                self.assertEqual(
                    {finding.rule for finding in result.findings}, rules
                )

    def test_counterexample_can_exempt_the_declared_violation_exactly(self):
        for body in (
            '<!-- guard:counterexample -->\n'
            '<!-- guard:violation compound-lane roles=builder '
            'text="Acme Builder" -->\n'
            "Hand it to the Acme Builder.\n"
            "<!-- /guard:counterexample -->\n",
            '<!-- guard:counterexample -->\n'
            '<!-- guard:violation branch-namespace roles=builder '
            'text="acme/some-scope" -->\n'
            "Cut `acme/some-scope` for this branch.\n"
            "<!-- /guard:counterexample -->\n",
        ):
            with self.subTest(body=body):
                self.assertEqual(
                    neutrality.scan(body, ("builder", "verifier")).findings,
                    [],
                )

        normalised = (
            '<!-- guard:counterexample -->\n'
            '<!-- guard:violation compound-lane roles=builder '
            'text="  `Acme   Builder`  " -->\n'
            "Hand it to the Acme Builder.\n"
            "<!-- /guard:counterexample -->\n"
        )
        self.assertEqual(
            neutrality.scan(normalised, ("builder", "verifier")).findings,
            [],
            "only presentation whitespace and outer backticks are ignored",
        )

    def test_branch_counterexample_names_the_same_branch_in_command_and_prose(self):
        command = "git checkout -b acme/some-scope origin/main"
        prose = "Create branch `acme/some-scope` for this round."
        for body in (command, prose):
            with self.subTest(body=body):
                findings = neutrality.scan(body, ("builder",)).findings
                self.assertEqual(
                    [finding.matched for finding in findings], ["acme/some-scope"]
                )
                declaration = (
                    '<!-- guard:counterexample -->\n'
                    '<!-- guard:violation branch-namespace roles=builder '
                    'text="acme/some-scope" -->\n'
                    f"{body}\n<!-- /guard:counterexample -->\n"
                )
                self.assertEqual(
                    neutrality.scan(declaration, ("builder",)).findings, []
                )

    def test_paragraph_findings_use_the_line_where_the_match_starts(self):
        cases = (
            (
                "Introductory text with no finding.\n"
                "Hand this to the Acme\n"
                "Builder today.",
                "compound-lane",
                2,
            ),
            (
                "Introductory text with no finding.\n"
                "Route this through vendor-builder lane.",
                "prefixed-lane",
                2,
            ),
        )
        for text, rule, expected_line in cases:
            with self.subTest(rule=rule):
                finding = next(
                    finding for finding in neutrality.scan(text, ("builder",)).findings
                    if finding.rule == rule
                )
                self.assertEqual(finding.line, expected_line)

    def test_partial_counterexample_declarations_do_not_exempt_any_rule(self):
        """A declaration is an exact matched-token key, never a substring."""
        cases = (
            (
                "compound-lane", "Builder", "Hand it to the Acme Builder.", {},
            ),
            (
                "prefixed-lane", "builder", "Use the `nebula-builder` queue.", {},
            ),
            (
                "branch-namespace", "nebula",
                "Create branch `nebula/release` for this round.", {},
            ),
            (
                "queue-identity", "nebula",
                "The live queue is docs/queue/nebula/active.md.",
                {"queue_pattern": r"docs/queue/([a-z]+)/"},
            ),
            (
                "lane-count", "three", "There are three standing lanes.",
                {"max_lanes": 2},
            ),
            (
                "compound-lane", "Acme Builder extra",
                "Hand it to the Acme Builder extra.", {},
            ),
        )
        for rule, declared, body, options in cases:
            text = (
                '<!-- guard:counterexample -->\n'
                f'<!-- guard:violation {rule} roles=builder text="{declared}" -->\n'
                f"{body}\n"
                "<!-- /guard:counterexample -->\n"
            )
            with self.subTest(rule=rule, declared=declared):
                result = neutrality.scan(
                    text, ("builder", "verifier"), **options
                )
                self.assertTrue(
                    any(f.rule == rule for f in result.findings),
                    f"partial/long declaration incorrectly exempted {rule}: "
                    f"{result.findings}",
                )

    def test_counterexample_declaration_must_be_present_and_true(self):
        cases = (
            "Hand it to the Acme Builder.\n",
            '<!-- guard:violation compound-lane roles=builder text="Absent Builder" -->\n'
            "Hand it to the Acme Builder.\n",
            '<!-- guard:violation prefixed-lane roles=builder text="Hand it to the Acme Builder." -->\n'
            "Hand it to the Acme Builder.\n",
            '<!-- guard:violation branch-namespace roles=builder text="The queue is ordinary." -->\n'
            "The queue is ordinary.\n",
        )
        for body in cases:
            with self.subTest(body=body):
                self.assertEqual(
                    neutrality.scan_counterexample(body, ("builder", "verifier")),
                    [],
                )

    def test_counterexample_declaration_must_match_its_own_finding(self):
        body = (
            '<!-- guard:violation compound-lane roles=builder text="harmless" -->\n'
            "This is harmless prose.\n"
            "Hand it to the Acme Builder.\n"
        )
        self.assertEqual(
            neutrality.scan_counterexample(body, ("builder", "verifier")), []
        )

    def test_framework_topologies_counterexample_is_noninert_for_builder_verifier(self):
        text = (ROOT / "framework" / "topologies.md").read_text(encoding="utf-8")
        blocks, _ = textblocks.counterexample_blocks(text)
        self.assertTrue(blocks, "topologies.md must contain a counterexample block")
        findings = [
            finding
            for _, body in blocks
            for finding in neutrality.scan_counterexample(
                body, ("builder", "verifier")
            )
        ]
        self.assertTrue(findings, "topologies.md counterexample became inert")

    def test_scan_records_an_unlisted_specialist_counterexample_as_noninert(self):
        text = (
            "<!-- guard:counterexample -->\n"
            '<!-- guard:violation compound-lane roles=decomper '
            'text="Claude Decomper" -->\n'
            "- `Claude Decomper` as a lane.\n"
            "<!-- /guard:counterexample -->\n"
        )
        result = neutrality.scan(text, ("builder",))
        self.assertTrue(result.counterexamples[0].findings)
        self.assertEqual(result.inert_counterexamples(), [])

    def test_adapters_do_not_redefine_the_contract(self):
        problems: list[str] = []
        for path in docset.normative_files():
            problems += [
                str(f) for f in neutrality.scan_adapter_blocks(
                    path.read_text(encoding="utf-8"),
                    source=path.relative_to(ROOT).as_posix(),
                )
            ]
        self.assertEqual(problems, [], "\n".join(problems))


class TestCounterexampleBlockOwnership(unittest.TestCase):
    """Symmetric to authority.py's own proof: a block genuinely owned by
    authority.py (`routine-approval` / `executor-self-merge`) must not be
    judged "inert" here -- but a block this scanner genuinely does own, and
    that genuinely exempts nothing, must still be caught.
    """

    def _scan(self, text: str) -> neutrality.ScanResult:
        return neutrality.scan(text, ROLES, coordinator=COORDINATOR)

    def test_a_block_declaring_only_an_authority_rule_is_not_inert_here(self):
        body = (
            '<!-- guard:counterexample -->\n'
            '<!-- guard:violation routine-approval roles=builder '
            'text="Brain reviews carefully." -->\n'
            "Brain reviews carefully.\n"
            "<!-- /guard:counterexample -->\n"
        )
        self.assertEqual(
            self._scan(body).inert_counterexamples(), [],
            "a block this scanner does not own was reported as this "
            "scanner's own inert exemption",
        )

    def test_a_block_this_scanner_genuinely_owns_and_exempts_nothing_is_still_caught(self):
        body = (
            '<!-- guard:counterexample -->\n'
            '<!-- guard:violation compound-lane roles=builder '
            'text="Acme Builder" -->\n'
            "This sentence does not actually say that.\n"
            "<!-- /guard:counterexample -->\n"
        )
        result = self._scan(body)
        self.assertEqual(
            len(result.inert_counterexamples()), 1,
            "a block genuinely declared for this scanner's own rule, that "
            "exempts nothing real, must still be caught",
        )

    def test_a_block_this_scanner_genuinely_owns_and_does_exempt_something_is_clean(self):
        body = (
            '<!-- guard:counterexample -->\n'
            '<!-- guard:violation compound-lane roles=builder '
            'text="Acme Builder" -->\n'
            "Hand this to the Acme Builder.\n"
            "<!-- /guard:counterexample -->\n"
        )
        result = self._scan(body)
        self.assertEqual(result.inert_counterexamples(), [])
        self.assertEqual(result.findings, [])


class TestGrammarAllowanceCannotBecomeAVendorList(unittest.TestCase):
    """The one allowance in the scanner, guarded."""

    def test_every_qualifier_is_a_lowercase_word(self):
        for word in neutrality.GRAMMAR_QUALIFIERS:
            with self.subTest(word=word):
                self.assertEqual(word, word.lower())
                self.assertTrue(
                    word.replace("'", "").isalpha(),
                    "qualifiers are English function words, not identifiers",
                )

    def test_no_known_provider_smuggled_in(self):
        """Secondary layer, and deliberately so.

        This is the only place a provider name appears, and it guards the
        exemption list rather than the documents. The structural rules do the
        real work; deleting this would weaken the guard but not break its
        architecture.
        """
        for name in ("claude", "anthropic", "codex", "openai", "gpt", "gemini",
                     "google", "grok", "xai", "copilot", "llama", "mistral"):
            with self.subTest(name=name):
                self.assertNotIn(name, neutrality.GRAMMAR_QUALIFIERS)


class TestNovelProviderIsRejected(unittest.TestCase):
    """The demonstration: a name nobody has seen is still rejected."""

    def test_the_novel_name_is_absent_from_the_scanner(self):
        source = (ROOT / "tools" / "neutrality.py").read_text(encoding="utf-8")
        self.assertNotIn(
            NOVEL.lower(), source.lower(),
            "the scanner must not know this name; if it does, this test proves "
            "nothing about future providers",
        )

    def test_the_novel_name_is_absent_from_the_documents(self):
        # If it were already in the tree, "it gets rejected" would prove nothing.
        hits = [
            p.relative_to(ROOT).as_posix()
            for p in docset.all_documents()
            if NOVEL.lower() in p.read_text(encoding="utf-8").lower()
        ]
        self.assertEqual(hits, [], f"{NOVEL} is no longer novel: {hits}")

    def _scan(self, text: str) -> neutrality.ScanResult:
        return neutrality.scan(
            text, ROLES, coordinator=COORDINATOR,
            queue_pattern=r"docs/queue/(?!archive/)([\w.-]+)\.md",
            max_lanes=len(ROLES),
        )

    def test_compound_lane_is_rejected(self):
        result = self._scan(f"Hand the brief to the {NOVEL} Worker this round.")
        self.assertTrue(
            any(f.rule == "compound-lane" for f in result.findings), result.report()
        )

    def test_prefixed_lane_token_is_rejected(self):
        result = self._scan("The live queue is docs/queue/nebula-worker.md for now.")
        rules = {f.rule for f in result.findings}
        self.assertIn("prefixed-lane", rules, result.report())
        self.assertIn("queue-identity", rules, result.report())

    def test_provider_branch_namespace_is_rejected(self):
        result = self._scan(
            "Cut your branch: git switch -c nebula/worker-task origin/main"
        )
        self.assertTrue(
            any(f.rule == "branch-namespace" for f in result.findings), result.report()
        )

    def test_provider_backticked_branch_is_rejected(self):
        result = self._scan("Use the branch `nebula/some-scope` for this round.")
        self.assertTrue(
            any(f.rule == "branch-namespace" for f in result.findings), result.report()
        )

    def test_provider_does_not_add_a_lane(self):
        result = self._scan(
            f"This round runs {len(ROLES) + 1} standing lanes across the providers."
        )
        self.assertTrue(
            any(f.rule == "lane-count" for f in result.findings), result.report()
        )

    def test_adapter_block_may_not_redefine_the_contract(self):
        problems = neutrality.scan_adapter_blocks(
            f"OPTIONAL — {NOVEL} only. Ignore otherwise.\n"
            "Then run: git switch -c nebula/other origin/main\n"
        )
        self.assertTrue(problems, "an adapter block redefining a branch was allowed")

    def test_a_role_lane_on_a_novel_tool_is_ACCEPTED(self):
        """The positive half, and the whole point.

        An unknown future tool holding a role needs no framework change. Only
        provider-SHAPED lanes are rejected.
        """
        accepted = (
            f"Run this round on {NOVEL}. You are the **Worker**. Cut your "
            "branch: git switch -c worker/some-scope origin/main. "
            "Your queue is docs/queue/worker.md."
        )
        result = self._scan(accepted)
        self.assertEqual(
            [str(f) for f in result.findings], [],
            "a role-named lane must be accepted whichever tool runs it",
        )



if __name__ == "__main__":
    unittest.main()
