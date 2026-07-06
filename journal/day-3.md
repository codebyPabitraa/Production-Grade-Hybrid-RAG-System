# Day 3

## Primary Goal

Continue from the benchmarked baseline and push the project from "working and documented" into "easy to inspect and improve".

The focus for Day 3 is likely to be:

- finer retrieval debugging
- more targeted corpus tuning
- optional chunking adjustments if they help measurable quality
- keeping the benchmark workflow stable

## Starting Point

We are starting Day 3 from a healthy milestone:

- the CLI works
- retrieval traces are visible
- BM25 and dense component traces are visible
- benchmark runs succeed
- comparison reports are generated
- the README and system design docs are filled in
- the journal now captures the full build history

That means the next step is refinement, not rescue.

## Current Baseline

The latest benchmark run showed:

- the pipeline is functioning end to end
- the retrieved context is visible and understandable
- the benchmark metrics are stable enough to compare
- the project is now a usable baseline for future tuning

The remaining room for improvement is mostly around retrieval precision and answer faithfulness on a few questions, not the basic architecture.

## What We Learned Before Day 3

- BM25 is strong on exact wording in this corpus.
- Dense retrieval helps, but the current dataset is still relatively small.
- Adding targeted source notes helps more than broad generic text.
- Retrieval inspection is now a much better debugging tool than guessing from answer text alone.
- The benchmark workflow is valuable because it exposes weaknesses clearly.

## Day 3 Plan

Possible next moves:

1. Inspect the weakest benchmark questions again and decide whether to tune chunking or keep adding targeted notes.
2. Improve chunk boundaries if a question is being split in a way that hurts retrieval.
3. Add a slightly more formal benchmark history summary if we want this version to become the long-term baseline.

## Status

Day 3 begins with the project in a good state:

- stable
- documented
- benchmarked
- debuggable

That is a solid base to continue from.

## Work Added After The First Day 3 Pass

### 1. Tightened The Answer Style

We reduced answer length and made the generation layer more direct.

That helped the benchmark because the answers stopped repeating themselves and stayed closer to the question.

### 2. Removed Meta Phrasing From Output

We noticed some model responses still included wording like `Context 2` or `Reference:`.

We added a small cleanup step so the final answer reads more naturally and focuses on the actual answer instead of the scaffold around it.

### 3. Observed A Better Benchmark Shape

The latest benchmark output showed:

- stronger faithfulness
- improved answer structure
- more direct answers for the most important project questions

That means the project is still improving, even though the architecture itself is already stable.

### 4. Started A Lightweight Benchmark Dashboard

We added a static HTML dashboard generator that summarizes the latest benchmark run and recent history.

This is intentionally lightweight:

- no new web framework
- no server to manage
- just a generated HTML file in `reports/`

The dashboard gives us a more visual way to inspect:

- latest benchmark metrics
- recent question-level scores
- whether the project is trending in the right direction

That makes the reporting layer more useful without adding much complexity.

### 5. Added Trend Bars To The Dashboard

We made the dashboard more visual by adding:

- score bars for each metric
- a simple delta indicator against the previous run
- a small legend that explains the visual language

That gives us a faster way to spot whether the latest run improved or regressed without opening the raw JSON reports first.

### 6. Added A PowerShell Dashboard Opener

We added a small PowerShell helper that:

- regenerates the benchmark dashboard
- opens it automatically in the browser

That makes the reporting workflow smoother on Windows and keeps the dashboard easy to use from the terminal.

### 7. Made The Dashboard Clickable

We linked the dashboard rows and latest report field back to the underlying JSON reports.

That means the dashboard now supports a simple workflow:

- glance at the summary
- click into the raw run report
- inspect the exact question, answer, and metrics

This makes the overview page more than just a pretty summary; it becomes a navigation tool for the benchmark data.

### 8. Hardened The Dashboard Test

The dashboard test now uses a tiny real report file instead of assuming links exist in an empty reports folder.

That makes the test match the actual dashboard behavior more closely and protects the clickable-report workflow we added.

### 9. Added A Private Interview Prep Note

We created a local-only interview prep file that includes:

- a two-minute project explanation
- likely interview questions
- short answer templates for common objections

We also added it to `.gitignore` so it stays private and does not get pushed to GitHub.

### 10. Made The Dashboard Interactive

We upgraded the dashboard from a summary page into an inspection page.

The latest version now lets us click a run and view:

- the full answer
- the retrieved context
- the detailed metrics for that run

That makes the UI much more useful for debugging and presenting the project.

### 11. Fixed The Dashboard Context Loader

We discovered that the dashboard was trying to read retrieved context from the wrong report field.

The saved reports store source chunks under `generated.sources`, so we updated the dashboard to rebuild the retrieved context from that data. That made the detail panel show the actual evidence used to answer the question instead of an empty placeholder.

### 12. Added Dashboard Filtering And Context Toggle

We made the dashboard easier to scan by adding:

- a run search box
- an exact-match toggle
- a show/hide toggle for retrieved context

That means the dashboard now supports faster navigation as the report history grows.

### 13. Added Row Highlighting And Copy Action

We polished the dashboard a bit further by:

- highlighting the selected run
- adding a copy button for the answer panel

This makes the inspection flow smoother when we want to compare answers or paste them elsewhere during review.

### 14. Fixed The Dashboard Test For Browser-Driven State

We corrected the dashboard test so it checks for the JavaScript behavior that adds the active-row styling, instead of expecting the active CSS class to appear in the static HTML.

That keeps the test aligned with how the dashboard actually works in the browser.

### 15. Reframed The Dashboard Around Metrics

We shifted the dashboard so the main visible focus is the evaluation data:

- context precision
- answer relevancy
- faithfulness
- context recall
- reference similarity

Raw report details and file paths were moved out of the primary visual flow so the page reads like a product UI instead of a file browser.

### 16. Cleaned Up The Dashboard Test Expectations

We removed an outdated assertion that expected the dashboard HTML to contain report links in the main view.

That test now matches the streamlined UI where metrics are the focus and file paths stay in the background.

### 17. Added Full Per-Run Report Pages

We added a dedicated HTML report page for every benchmark run.

Each report page now includes:

- the question
- the answer
- the evaluation metrics
- the retrieved context

The dashboard now links to those pages through a clear "Open report" action instead of exposing the raw JSON file path in the main UI.

We also updated the dashboard generator so it writes the report pages automatically whenever we regenerate the dashboard.

### 18. Added Export And Download Actions

We improved the run inspection flow by giving each benchmark run two direct actions:

- open the full report page
- download the HTML report

This keeps the UI focused on the metrics and answer quality while still making each run easy to share or archive locally.

### 19. Polished The Run Report Layout

We tightened the report page styling so it feels more like a finished product view:

- a stronger hero section
- summary chips for the run purpose
- better metric framing
- a clearer local HTML download action

That keeps the report readable for demos while still staying lightweight and fully static.

### 20. Added Report Page Navigation And Summary Strip

We improved the per-run page with:

- anchor links for metrics, answer, and retrieved context
- a compact summary strip
- a clearer top-metric callout

This makes the report easier to scan quickly during demos or interview walkthroughs.

### 21. Started The Local Upload-And-Ask Demo

We added a local HTTP demo server that lets us:

- upload files
- ask a question
- run the existing RAG pipeline end to end
- view the answer, metrics, retrieval trace, and saved report from one page

This is the first step toward turning the project into a real user-facing RAG app instead of only a benchmark and dashboard toolkit.

### 22. Added Admin-Governed Upload Storage

We changed the upload path so files no longer go straight into the active corpus.

Now the flow is:

- pending upload storage
- admin approval or rejection
- permanent approved corpus storage
- question answering only from approved files

We also tightened the answer prompt so hosted generation can explain answers more naturally instead of sounding too clipped.

### 23. Improved The Admin Queue And Answer Explanation

We made the admin page more readable by adding summary cards and recent approved/rejected previews.

We also added a "why this answer" section to the local app so users can see a short explanation of how the retrieved evidence supports the answer.

This should help the product feel more transparent during demos and interviews.

### 24. Added Approval Notes And An Approved Corpus Browser

We tightened the admin flow so each approval or rejection can include a review note.

We also added an approved corpus browser to the app so we can see which files are live in the system before asking questions against them.

### 25. Hid Backend Traces From The Public UI

We cleaned up the public app so it no longer surfaces raw retrieval traces or backend-style chunks in the user-facing flow.

Instead, the page now explains the RAG metrics up front and keeps the public experience focused on:

- the answer
- a short explanation of why it was generated
- the approved corpus browser

That makes the app look more like a real deployed product and less like an internal debugger.

### 26. Added Local Auth Foundations

We added a lightweight auth layer for the deployment path:

- JWT-style signed tokens
- email OTP verification for registration
- environment-based admin bootstrapping

This gives us a realistic path toward separate user/admin logins without adding a lot of infrastructure yet.

### 27. Added Logout Support

We added a logout endpoint that clears the auth cookie and returns the user to the public landing page.

That completes the basic sign-in and sign-out loop for the local demo.

### 28. Made The Signed-In State Visible

We improved the public page so it now clearly shows whether the user is signed in.

When signed in, it shows the active account and replaces the generic auth links with a logout action. That makes the session state much easier to understand during demos and testing.
