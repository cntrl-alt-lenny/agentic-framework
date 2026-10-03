"""Brain's independent issue #40 probe; creates only disposable repositories."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tests.helpers import fw, git  # noqa: E402
from tests.test_handoffs import HandoffRound  # noqa: E402


def main():
    case = HandoffRound()
    case.setUp()
    try:
        case.write_brief("210-reviewed")
        case.deliver_worker("worker", "210-reviewed")
        case.deliver_verifier("verifier", "210-reviewed")
        before = fw(case.brain, "delivery", "--round", "210-reviewed")
        print("Original delivery:", before.returncode)
        print(before.stdout)
        case.write_brief("211-next", start="origin/verifier/210-reviewed")
        brief_only = fw(case.brain, "delivery", "--round", "210-reviewed")
        print("Successor brief alone:", brief_only.returncode)
        print(brief_only.stdout)
        git(case.brain, "switch", "-q", "brain/211-next")
        record = case.brain / "docs/rounds/210-reviewed/attachments/brain-review.md"
        record.parent.mkdir(exist_ok=True)
        record.write_text("Brain independently checked the unchanged delivery.\n", encoding="utf-8")
        case.commit_all(case.brain, "Record review alongside next brief")
        git(case.brain, "push", "-q")
        after = fw(case.brain, "delivery", "--round", "210-reviewed")
        named = fw(case.brain, "delivery", "--round", "210-reviewed", "--branch", "origin/verifier/210-reviewed")
        print("Successor plus Brain review record:", after.returncode)
        print(after.stdout)
        print("Explicit unchanged delivery:", named.returncode)
        print(named.stdout)
        return 0 if all(result.returncode == 0 for result in (before, brief_only, after, named)) else 1
    finally:
        case.tearDown()


if __name__ == "__main__":
    sys.exit(main())
