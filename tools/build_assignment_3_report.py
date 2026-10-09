"""Build the Assignment 3 PDF from the published project evidence."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "Assignment_3_Software_Development_and_Integration_Alisher_Tokesh.pdf"
FONT_ROOT = Path("/System/Library/Fonts/Supplemental")
REPO = "https://github.com/Tsarkashrk/novelty-similarity-detection-model"
RUN = REPO + "/actions/runs/37891050872"
CI = REPO + "/blob/main/.github/workflows/ci.yml"
ISSUE = REPO + "/issues/1"
INK = colors.HexColor("#151515")
MUTED = colors.HexColor("#505050")
LINE = colors.HexColor("#D9D9D9")
HEADER = colors.HexColor("#E6EDF3")


def register_fonts() -> None:
    for name, filename in (
        ("TNR", "Times New Roman.ttf"),
        ("TNR-Bold", "Times New Roman Bold.ttf"),
        ("TNR-Italic", "Times New Roman Italic.ttf"),
        ("TNR-BoldItalic", "Times New Roman Bold Italic.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(FONT_ROOT / filename)))
    pdfmetrics.registerFontFamily(
        "TNR", normal="TNR", bold="TNR-Bold", italic="TNR-Italic", boldItalic="TNR-BoldItalic"
    )


def page_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("TNR", 10)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(A4[0] / 2, 32, f"Assignment 3  |  Alisher Tokesh  |  {doc.page}")
    canvas.restoreState()


def make_styles() -> dict[str, ParagraphStyle]:
    base = dict(fontName="TNR", textColor=INK, allowWidows=0, allowOrphans=0)
    return {
        "body": ParagraphStyle(
            "Body", fontSize=12, leading=18, alignment=TA_JUSTIFY, spaceAfter=8, **base
        ),
        "body_last": ParagraphStyle(
            "Body Last", fontSize=12, leading=18, alignment=TA_JUSTIFY, spaceAfter=0, **base
        ),
        "title": ParagraphStyle(
            "Title", fontName="TNR-Bold", fontSize=20, leading=27, alignment=TA_CENTER,
            textColor=INK, spaceAfter=15,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", fontSize=14, leading=21, alignment=TA_CENTER, spaceAfter=12, **base
        ),
        "h1": ParagraphStyle(
            "Heading 1", fontName="TNR-Bold", fontSize=15, leading=20, alignment=TA_LEFT,
            textColor=INK, spaceBefore=0, spaceAfter=12, keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "Heading 2", fontName="TNR-Bold", fontSize=12, leading=18, alignment=TA_LEFT,
            textColor=INK, spaceBefore=9, spaceAfter=5, keepWithNext=True,
        ),
        "toc": ParagraphStyle(
            "Contents", fontSize=12, leading=19, alignment=TA_LEFT, spaceAfter=2, **base
        ),
        "table": ParagraphStyle(
            "Table", fontSize=12, leading=16, alignment=TA_LEFT, spaceAfter=0, **base
        ),
        "table_head": ParagraphStyle(
            "Table Header", fontName="TNR-Bold", fontSize=12, leading=16,
            alignment=TA_LEFT, textColor=INK,
        ),
        "caption": ParagraphStyle(
            "Caption", fontName="TNR-Italic", fontSize=12, leading=18,
            alignment=TA_CENTER, textColor=MUTED, spaceBefore=5, spaceAfter=12,
        ),
        "ref": ParagraphStyle(
            "Reference", fontSize=12, leading=18, alignment=TA_LEFT, spaceAfter=5, **base
        ),
    }


def link(text: str, url: str) -> str:
    return f'<link href="{escape(url, {"\"": "&quot;"})}" color="#174A70">{escape(text)}</link>'


def add_body(story, styles, text: str, *, last: bool = False) -> None:
    story.append(Paragraph(text, styles["body_last" if last else "body"]))


def add_heading(story, styles, text: str, level: int = 1) -> None:
    story.append(Paragraph(escape(text), styles[f"h{level}"]))


def add_table(story, styles, headers, rows, widths, caption: str) -> None:
    data = [[Paragraph(escape(h), styles["table_head"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(value, styles["table"]) for value in row])
    table = Table(data, colWidths=widths, hAlign="CENTER", repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HEADER),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FB")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Paragraph(escape(caption), styles["caption"]))


def build() -> None:
    register_fonts()
    styles = make_styles()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    width, height = A4
    left, right, top, bottom = 64, 58, 59, 55
    doc = BaseDocTemplate(
        str(OUT), pagesize=A4, leftMargin=left, rightMargin=right,
        topMargin=top, bottomMargin=bottom,
        title="Software Development and Integration for a Novelty Similarity Detection Model",
        author="Alisher Tokesh",
        subject="Applied Software Development Project Assignment 3",
    )
    frame = Frame(
        left, bottom, width - left - right, height - top - bottom,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates(PageTemplate(id="report", frames=[frame], onPage=page_footer))
    story = []

    # Page 1 - title.
    story.append(Spacer(1, 118))
    story.append(Paragraph("Applied Software Development Project", styles["subtitle"]))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Software Development and Integration for a Novelty Similarity Detection Model", styles["title"]))
    story.append(Spacer(1, 21))
    story.append(Paragraph("Assignment 3", styles["subtitle"]))
    story.append(Paragraph("Alisher Tokesh  |  CSE-2507M", styles["subtitle"]))
    story.append(Spacer(1, 132))
    story.append(Paragraph("Continuation of Assignments 1 and 2", styles["subtitle"]))
    story.append(Paragraph("9 October 2026", styles["subtitle"]))
    story.append(PageBreak())

    # Page 2 - contents and scope.
    add_heading(story, styles, "Contents")
    for text, number in [
        ("1 Project context and development process", 3),
        ("2 Selection of technologies and tools", 4),
        ("3 Version control and GitHub collaboration", 5),
        ("4 Continuous integration and delivery", 6),
        ("5 Scientific software development", 7),
        ("6 Practical module and repository evidence", 8),
        ("7 Conclusions and recommendations", 9),
        ("References", 9),
    ]:
        story.append(Paragraph(f"{escape(text)} {'.' * max(4, 57 - len(text))} {number}", styles["toc"]))
    story.append(Spacer(1, 17))
    add_heading(story, styles, "Executive summary", 2)
    add_body(story, styles, "This report continues the same thesis-topic novelty screening project assessed in Assignments 1 and 2. Assignment 1 established a 17-week critical path, USD 38,188 in direct cost, a USD 5,728 contingency reserve, and a USD 43,916 planned budget. Assignment 2 recommended stage-gated iterative research and development and a modular monolith with explicit adapters. The present assignment turns those choices into a version-controlled scientific software module with a public repository, automated tests, an issue workflow, and a working CI pipeline.")
    add_body(story, styles, "The module accepts a proposed title, abstract, keywords, domain, and language. It combines semantic similarity, keyword uniqueness, and domain rarity into an explainable novelty assessment. The current prototype uses in-memory retrieval; the planned pgvector integration is tracked as a future task. A high similarity result is a reviewer prompt, not an automatic academic rejection.")
    add_body(story, styles, "The public repository is " + link("github.com/Tsarkashrk/novelty-similarity-detection-model", REPO) + ". The tested workflow is " + link("GitHub Actions run 37891050872", RUN) + ".", last=True)
    story.append(PageBreak())

    # Page 3 - process and organization.
    add_heading(story, styles, "1 Project context and development process")
    add_body(story, styles, "A software process converts a research idea into a maintainable service through defined requirements, design, implementation, verification, release, and feedback. In this project, each stage produces evidence that an academic reviewer can inspect. The process is iterative because multilingual retrieval and threshold choices depend on corpus quality and labelled examples; it is stage-gated because student-facing decisions require explicit approval of data access, model quality, security, and pilot readiness.")
    add_table(story, styles, ["Stage", "Output", "Decision evidence"], [
        ["Requirements and data", "Topic fields, duplicate policy, data access approval", "Approved scope and labelled-pair protocol"],
        ["Design and implementation", "Hybrid scorer, API contract, repository boundary", "Runnable vertical slice and code review"],
        ["Verification", "Unit tests, integration plan, quality and latency measurements", "F1, near-duplicate recall and error samples"],
        ["Pilot and release", "Reviewer workflow, training and monitored deployment", "Human-review record and rollout decision"],
    ], [112, 178, 185], "Table 1  Deliverables and evidence across the 17-week plan")
    add_body(story, styles, "The critical path from Assignment 1 runs through requirements (A), data approval (B), baseline adaptation (D), backend integration (F), coordinator workflow (G), QA (H), pilot (I), deployment (J), and closure (K). Corpus preparation (C) and calibration (E) have limited slack, so their work can be refined in short cycles without losing sight of the fixed finish date. Weekly reviews should compare the Gantt baseline with actual progress and log decisions that consume reserve funds.")
    add_body(story, styles, "Responsibilities follow the WBS: the academic lead owns the duplicate policy and final approval; the data owner authorizes and validates the corpus; ML and backend engineers implement the model and service; QA and domain reviewers test behavior and examine false high-risk flags. A definition of done for each increment includes a passing test, versioned inputs, an explanation of results, and a named reviewer for any academic-risk decision.", last=True)
    story.append(PageBreak())

    # Page 4 - technology choices.
    add_heading(story, styles, "2 Selection of technologies and tools")
    add_body(story, styles, "Technology selection should be driven by functional fit, scientific reproducibility, team skill, integration cost, operating cost, security, and the ability to replace a component later. The 17-week schedule and USD 43,916 cap favor a small deployable service. A technology earns its place when it makes a measurable requirement easier to satisfy; novelty alone does not justify additional infrastructure.")
    add_table(story, styles, ["Choice", "Rationale", "Trade-off and control"], [
        ["Python 3.10+", "Existing code, NLP ecosystem, typed dataclasses and simple packaging", "Runtime speed is lower than compiled languages; benchmark hot paths"],
        ["FastAPI", "Existing assessment endpoint and machine-readable API boundary", "Add platform authentication and contract tests before pilot"],
        ["Hashing backend", "Deterministic and dependency-light CI baseline", "Not a claim of multilingual semantic quality"],
        ["Multilingual E5", "Multilingual embeddings for Russian, Kazakh and English topics", "Model download, compute cost and language-specific evaluation"],
        ["PostgreSQL + pgvector", "Planned persistent top-k search using an existing schema", "Current prototype remains in memory; adapter and load tests are pending"],
    ], [118, 176, 181], "Table 2  Technology decisions against project goals")
    add_body(story, styles, "The packaging file <i>pyproject.toml</i> keeps the core dependency-free and groups API, embedding, experiment, and development tools as optional extras. This supports two environments: a small deterministic CI environment for fast feedback and a controlled research environment with a pinned embedding model and labelled validation data. The boundary around <i>EmbeddingBackend</i> makes it possible to compare encoders without rewriting the scoring policy.")
    add_body(story, styles, "Before changing the model or database, the team should record corpus version, language distribution, embedding model identifier, vector dimension, thresholds, and evaluation results. That record connects engineering changes to the KPIs from Assignment 2: duplicate F1 at least 0.82, near-duplicate recall at least 0.75, false high-risk rate at most 8 percent, and top-k latency at most 1.5 seconds. These are pilot targets, not measured achievements of the current CI run.", last=True)
    story.append(PageBreak())

    # Page 5 - version control.
    add_heading(story, styles, "3 Version control and GitHub collaboration")
    add_body(story, styles, "Git records source changes as commits in a distributed history. It supports local branches, reviewable differences, and recovery of earlier versions. GitHub hosts the Git repository and adds pull requests, issues, access controls, and automation; it is a collaboration platform rather than a separate version control algorithm. Subversion (SVN) is a useful comparison because it keeps the authoritative history on one central server. For a research module with experiments and a small team, Git's cheap local branches and reproducible commit identifiers are a strong fit.")
    add_table(story, styles, ["Capability", "Git", "SVN", "GitHub platform"], [
        ["History", "Complete local clone", "Central server", "Remote Git hosting"],
        ["Offline work", "Commit and inspect locally", "Limited without server", "Depends on Git locally"],
        ["Review", "Diff and merge tools", "Diff and merge tools", "Pull requests and checks"],
        ["Project tasks", "No built-in issue tracker", "No built-in issue tracker", "Issues and templates"],
    ], [95, 130, 110, 140], "Table 3  Version control and collaboration comparison")
    add_body(story, styles, "The repository uses a <i>main</i> branch and a public remote. A normal change should begin with a focused issue, use a short-lived branch, include a test or reproducible example, and be reviewed before merge. The README documents local setup and the meaning of the CI badge. The MIT license states reuse terms. Two issue templates request reproducible bug evidence or explicit acceptance evidence for research tasks, while warning contributors not to post private student data.")
    add_body(story, styles, "For this assignment, commit <b>897960e</b> published the workflow, license, issue templates, README update, and CLI test. " + link("Issue 1", ISSUE) + " tracks the future pgvector repository adapter with integration-test criteria. This keeps unfinished production work visible without presenting it as implemented. Git tags can later mark a validated release, with the corresponding model configuration and corpus version recorded alongside it.", last=True)
    story.append(PageBreak())

    # Page 6 - CI/CD.
    add_heading(story, styles, "4 Continuous integration and delivery")
    add_body(story, styles, "Continuous integration (CI) runs automated checks whenever changes enter the shared history. It reduces the delay between introducing an error and finding it. Continuous delivery (CD) prepares a tested release candidate so a human can approve deployment; continuous deployment additionally releases each passing change automatically. Academic approval and private-data access make a manual promotion gate appropriate for this pilot.")
    add_table(story, styles, ["Trigger", "Automated gate", "Output"], [
        ["Push to main or pull request", "Install package, run unit and CLI tests on Python 3.10 and 3.12; compile source", "Pass or fail status visible on GitHub"],
        ["Successful push to main", "Build a wheel only after both test jobs succeed", "Versioned package candidate"],
        ["Successful package job", "Upload the wheel as a workflow artifact", "Downloadable artifact for manual review"],
    ], [132, 210, 133], "Table 4  Implemented CI and delivery-candidate path")
    add_body(story, styles, "The YAML workflow is stored at " + link(".github/workflows/ci.yml", CI) + ". Its job dependency enforces the order: test first, package second. The token is restricted to read-only repository contents. This avoids a workflow that can publish or deploy without approval. A dependency cache speeds repeated Python jobs, while the wheel artifact preserves the exact build output of a successful run.")
    add_body(story, styles, "The first public run, " + link("run 37891050872", RUN) + ", completed successfully for commit 897960e. The Python 3.10 test job, Python 3.12 test job, and package job all passed, and the <i>thesis-novelty-wheel</i> artifact was uploaded. Locally, the same three automated tests passed and a wheel was built. These checks prove packaging and baseline behavior; they do not prove multilingual model quality, secure institutional access, or production latency. Those remain explicit quality gates in the 17-week project plan.", last=True)
    story.append(PageBreak())

    # Page 7 - scientific software.
    add_heading(story, styles, "5 Scientific software development")
    add_body(story, styles, "Scientific software must make a claim reproducible. For a novelty detector, a score is meaningful only with its input corpus, preprocessing rules, embedding model, weights, thresholds, and labelled evaluation protocol. The requirements therefore combine ordinary software behavior (valid API responses and stable packaging) with research behavior (traceable experiments, error analysis, and performance by language). A passing test suite cannot substitute for a representative validation set.")
    add_heading(story, styles, "Environments and libraries", 2)
    add_body(story, styles, "The core Python package uses standard-library dataclasses and a deterministic hashing embedding backend. This keeps CI fast and allows tests to run without a large model download. FastAPI and Pydantic are optional service dependencies; SentenceTransformers supplies research-grade multilingual embeddings when enabled; pandas, scikit-learn, and matplotlib are optional experiment tools. A production-like environment must pin exact versions and model identifiers, record the corpus revision, and prohibit real student records in public fixtures.")
    add_heading(story, styles, "Verification beyond unit tests", 2)
    add_body(story, styles, "Unit tests check duplicate and unrelated-topic behavior. The CLI smoke test checks the public command, JSON structure, and explanation components with synthetic sample data. The next layer should test an API contract, a pgvector repository adapter, migration and restart behavior, and retrieval agreement against the in-memory baseline. Evaluation should report precision, recall, F1, false high-risk rate, and calibration by Russian, Kazakh, and English topic subsets. Timing tests should use the expected pilot corpus rather than the ten-row sample CSV.")
    add_body(story, styles, "The scientific risk is a false sense of validity: a deterministic baseline may pass CI while semantic quality remains weak. The mitigation is to freeze a labelled benchmark before tuning, compare baselines with multilingual embeddings, keep an error log for disputed cases, and require a human reviewer before any high-risk topic is rejected. Such practices make the research result testable and align the code with the academic governance defined in Assignments 1 and 2.", last=True)
    story.append(Spacer(1, 9))
    add_heading(story, styles, "Reproducibility controls", 2)
    add_body(story, styles, "Each experiment should record the Git commit, dependency versions, model identifier, corpus hash, language mix, threshold settings, and exact evaluation script. Data should be split before tuning so near-duplicate pairs from the same topic family do not leak into both development and test sets. A failed quality gate should produce an issue with a synthetic reproduction case and a named owner, then be rechecked against the unchanged benchmark.", last=True)
    story.append(PageBreak())

    # Page 8 - practical module.
    add_heading(story, styles, "6 Practical module and repository evidence")
    add_body(story, styles, "The practical module is the existing <i>thesis_novelty</i> package, now documented and checked by CI. A CSV loader creates historical topic records. Preprocessing and an embedding backend encode query and corpus text. The model ranks candidates by cosine similarity, calculates keyword uniqueness and domain rarity, combines the three components with default weights 0.60, 0.25, and 0.15, and returns a label plus explanation. The CLI and FastAPI adapter expose the result. Default similarity cutoffs are 0.90 for duplicate and 0.75 for near-duplicate.")
    add_table(story, styles, ["Repository component", "Current function", "Assignment 2 boundary"], [
        ["model.py", "Hybrid scoring and in-memory top-k ranking", "Keep scoring independent from storage"],
        ["embeddings.py", "Interchangeable hashing and SentenceTransformer backends", "Replace model without changing use case"],
        ["api.py and cli.py", "Service and command-line adapters", "Expose a stable assessment contract"],
        ["test_model.py and test_cli.py", "Behavior and command-line checks", "Extend to storage and API integration"],
    ], [162, 178, 135], "Table 5  Small scientific module and intended evolution")
    add_body(story, styles, "The public " + link("repository", REPO) + " includes README instructions, the MIT license, two issue templates, the CI workflow, sample topics, labelled pairs, source code, tests, and the pgvector schema. The " + link("Actions run", RUN) + " provides independent evidence that the committed state passes its automated gates. The " + link("pgvector issue", ISSUE) + " records a concrete next step with acceptance tests. These links let an instructor inspect both the software and the process.")
    add_body(story, styles, "The practical work deliberately stops at a delivery candidate. It does not claim that pgvector is connected, that student data has been approved, or that the university platform is deployed. These gaps correspond to WBS work packages 1.2, 1.4, 1.5, and 1.6 from Assignment 1 and to the ports and quality attributes assessed in Assignment 2.", last=True)
    story.append(PageBreak())

    # Page 9 - outcome, challenges, references.
    add_heading(story, styles, "7 Conclusions and recommendations")
    add_body(story, styles, "The assignment produced a public, version-controlled scientific module with documented technology choices, a license, issue tracking, automated tests, and a successful CI run that builds a wheel. Python, FastAPI, replaceable embedding backends, and a future pgvector adapter fit the project because they preserve explainability and allow the team to test each uncertain component. The GitHub workflow gives immediate integration feedback and a candidate package while retaining the manual release decision required by academic review.")
    add_body(story, styles, "One challenge encountered was that a title-only CLI test did not reproduce an exact duplicate: the model also embeds the abstract, keywords, and domain. The test was corrected to provide the complete public fixture, which makes the check reflect the actual input contract. Another boundary is that the current three-test suite and hashing fallback are engineering smoke checks, not the multilingual validation required for the pilot. The next increment should use the labelled corpus and per-language metrics, then add storage and API integration tests before deploying to coordinators.")
    add_body(story, styles, "Recommendation: keep the 17-week and USD 43,916 baselines from Assignment 1, use the stage-gated iterative method and modular boundaries from Assignment 2, and require passing quality, security, latency, and human-review gates before production rollout. The current CI result supports continued development; a release decision still depends on measured model and workflow outcomes.")
    add_heading(story, styles, "References", 2)
    refs = [
        "1. Tokesh, A. Assignment 1: Project Management and Financial Justification for a Novelty Similarity Detection Model. Course report, 2026.",
        "2. Tokesh, A. Assignment 2: Development Methodology and Architecture Assessment for a Novelty Similarity Detection Model. Course report, 2026.",
        "3. Hybrid Thesis Topic Novelty Assessment Model. " + link("Public repository", REPO) + ", commit 897960e; accessed 9 October 2026.",
        "4. Chacon, S. and Straub, B. Pro Git, chapter 1.1, " + link("About Version Control", "https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control.html") + ".",
        "5. GitHub Docs. " + link("Understanding GitHub Actions", "https://docs.github.com/en/actions/get-started/understanding-github-actions") + "; " + link("Workflow artifacts", "https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts") + ".",
        "6. Python Packaging Authority. " + link("The Packaging Flow", "https://packaging.python.org/en/latest/flow/") + ".",
    ]
    for ref in refs:
        story.append(Paragraph(ref, styles["ref"]))

    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    build()
