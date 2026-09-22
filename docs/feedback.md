# From feedback to release

How problems found while working on projects become framework changes — and
how most of them do not. The framework Brain follows this; nobody else needs
to read it.

## Where feedback arrives

- **GitHub issues** on this repository, from the "Framework feedback" form.
  Any device with a browser, and any agent with GitHub access, can file one.
- **Files** at `docs/framework-feedback/*.md` in a project, when the agent
  that found the problem could not reach GitHub. Brain copies each into an
  issue when it sees one, and links back.

Nothing else is a queue. An issue closed with a reason is the reply.

## Triage — every issue gets exactly one label

| Label | Meaning | What happens |
|---|---|---|
| `framework-defect` | Reproduced: the framework's text or tool is wrong | Fix it, in the next batch |
| `friction` | Reproduced: the framework works but costs measurable time | Fix only if the cost is shown, and the fix removes more than it adds |
| `project-config` | The project's own files or settings | Reply with the fix for the project; no framework change |
| `agent-error` | A model ignored a clear rule | No change, unless the same error appears in two or more projects |
| `docs` | The text is unclear, not wrong | Reword within the word budget |
| `wontfix` | A deliberate boundary, or not worth its cost | Close with the reason |

Add `required` only for a defect that makes projects produce wrong results or
lose work. Only `required` issues skip the batching and the freeze.

## The gates

1. **Reproduce first.** Run the reporter's commands at their project commit
   and framework release. An issue that cannot be reproduced is labelled
   `cannot-reproduce` and waits for more evidence; it changes nothing.
2. **Fix the class, not the example**, and say in the brief what the class is.
3. **Stay in budget.** `tests/test_docs.py` fails when the core or a role card
   grows past its word budget. Each release note states how many words and
   lines it added and removed.
4. **Prove it on a project shape.** `tests/test_adopt.py` migrates a
   2.x-shaped project on every run; add to that fixture when a defect came
   from a real project's layout.
5. **Batch.** At most one release every two weeks, then ten product rounds
   before the next, unless an issue is `required`.
6. **Release.** The owner says yes to the merge; Brain tags `vX.Y.Z` and adds
   the CHANGELOG entry with "What an adopter must do". Projects see the
   release in `fw.py status`; nobody needs to announce it.

Major versions change contracts or files and need an update before a
project's next round. Minor and patch releases can wait.
