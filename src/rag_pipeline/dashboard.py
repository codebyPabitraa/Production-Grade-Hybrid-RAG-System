from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from rag_pipeline.benchmark_history import build_history_index
from rag_pipeline.storage import reports_root


def _escape(text: Any) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _trend_delta(current: float, previous: float | None) -> tuple[str, str]:
    if previous is None:
        return ("neutral", "No prior run")
    delta = current - previous
    if abs(delta) < 1e-9:
        return ("neutral", "No change")
    direction = "up" if delta > 0 else "down"
    sign = "+" if delta > 0 else ""
    return (direction, f"{sign}{delta:.4f}")


def _metric_bar(value: float, max_value: float = 1.0) -> str:
    clamped = max(0.0, min(value / max_value, 1.0))
    return f'<div class="bar"><span style="width:{clamped * 100:.1f}%"></span></div>'


def _report_page_name(report_path: str) -> str:
    return f"{Path(report_path).stem}.html"


def _load_report_details(report_path: str) -> dict[str, Any]:
    path = Path(report_path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    generated = data.get("generated", {})
    evaluation = data.get("evaluation", {})
    sources = generated.get("sources", []) if isinstance(generated, dict) else []
    retrieved_context_lines: list[str] = []
    if isinstance(sources, list):
        for index, source in enumerate(sources, start=1):
            if not isinstance(source, dict):
                continue
            chunk = source.get("chunk", {})
            if not isinstance(chunk, dict):
                continue
            chunk_text = str(chunk.get("text", "")).strip()
            retrieved_context_lines.append(f"[Context {index}]\n{chunk_text}")
    return {
        "question": data.get("question", ""),
        "answer": data.get("answer", ""),
        "report_path": str(path),
        "report_href": f"report-pages/{_report_page_name(str(path))}",
        "timestamp_utc": data.get("timestamp_utc", ""),
        "retrieved_context": "\n\n".join(retrieved_context_lines),
        "context_precision": evaluation.get("context_precision", 0.0),
        "answer_relevancy": evaluation.get("answer_relevancy", 0.0),
        "faithfulness": evaluation.get("faithfulness", 0.0),
        "context_recall": evaluation.get("context_recall", 0.0),
        "reference_similarity": data.get("reference_similarity", 0.0),
    }


def build_dashboard_html(reports_dir: Path = reports_root(), limit: int = 10) -> str:
    index = build_history_index(reports_dir)
    runs = index.get("runs", [])[:limit]
    detailed_runs = []
    for run in runs:
        details = _load_report_details(run["report_path"])
        detailed_runs.append({**run, **details})
    runs = detailed_runs
    latest = runs[0] if runs else None
    previous = runs[1] if len(runs) > 1 else None
    metrics = latest.get("metrics", {}) if latest else {}
    previous_metrics = previous.get("metrics", {}) if previous else {}
    latest_question = latest.get("question", "No benchmark runs found") if latest else "No benchmark runs found"
    latest_report = latest.get("report_path", "") if latest else ""
    latest_answer = latest.get("answer", "") if latest else ""
    latest_context = latest.get("retrieved_context", "") if latest else ""

    cards = []
    for key, label in [
        ("context_precision", "Context Precision"),
        ("answer_relevancy", "Answer Relevancy"),
        ("faithfulness", "Faithfulness"),
        ("context_recall", "Context Recall"),
    ]:
        trend_class, trend_text = _trend_delta(metrics.get(key, 0.0), previous_metrics.get(key) if previous else None)
        cards.append(
            f"""
            <div class="card">
              <div class="label">{_escape(label)}</div>
              <div class="value">{metrics.get(key, 0.0):.4f}</div>
              {_metric_bar(metrics.get(key, 0.0))}
              <div class="trend {trend_class}">{_escape(trend_text)}</div>
            </div>
            """
        )

    rows = []
    detail_payload = []
    for run in runs:
        row_metrics = run["metrics"]
        report_href = f"report-pages/{_report_page_name(run['report_path'])}"
        payload = {
            "question": run.get("question", ""),
            "answer": run.get("answer", ""),
            "report_href": report_href,
            "timestamp_utc": run.get("timestamp_utc", ""),
            "context_precision": row_metrics["context_precision"],
            "answer_relevancy": row_metrics["answer_relevancy"],
            "faithfulness": row_metrics["faithfulness"],
            "context_recall": row_metrics["context_recall"],
            "reference_similarity": run.get("reference_similarity", 0.0),
            "retrieved_context": run.get("retrieved_context", ""),
        }
        detail_payload.append(payload)
        rows.append(
            f"""
            <tr class="run-row" data-index="{len(detail_payload) - 1}">
              <td>
                <div>{_escape(run["question"])}</div>
                <div class="small">
                  <a href="{_escape(report_href)}" target="_blank" rel="noopener">Open report</a>
                  <span aria-hidden="true"> · </span>
                  <a href="{_escape(report_href)}" download>Download</a>
                </div>
              </td>
              <td>{row_metrics["context_precision"]:.3f}</td>
              <td>{row_metrics["answer_relevancy"]:.3f}</td>
              <td>{row_metrics["faithfulness"]:.3f}</td>
              <td>{row_metrics["context_recall"]:.3f}</td>
            </tr>
            """
        )

    initial_detail = detail_payload[0] if detail_payload else {
        "question": latest_question,
        "answer": latest_answer,
        "report_path": latest_report,
        "timestamp_utc": latest.get("timestamp_utc", "") if latest else "",
        "context_precision": metrics.get("context_precision", 0.0),
        "answer_relevancy": metrics.get("answer_relevancy", 0.0),
        "faithfulness": metrics.get("faithfulness", 0.0),
        "context_recall": metrics.get("context_recall", 0.0),
        "reference_similarity": latest.get("reference_similarity", 0.0) if latest else 0.0,
        "retrieved_context": latest_context,
        "report_href": _report_page_name(latest_report) if latest_report else "",
    }

    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>RAG Benchmark Dashboard</title>
      <style>
        :root {{
          color-scheme: dark;
          --bg: #0e1117;
          --panel: #151a23;
          --panel-2: #10151d;
          --text: #e6edf3;
          --muted: #9aa4b2;
          --accent: #37d67a;
          --border: #243041;
        }}
        body {{
          margin: 0;
          font-family: Segoe UI, Arial, sans-serif;
          background: radial-gradient(circle at top, #172033, var(--bg) 55%);
          color: var(--text);
        }}
        .wrap {{
          max-width: 1180px;
          margin: 0 auto;
          padding: 32px 20px 48px;
        }}
        .hero {{
          display: grid;
          grid-template-columns: 1.5fr 1fr;
          gap: 18px;
          align-items: stretch;
        }}
        .panel {{
          background: linear-gradient(180deg, rgba(21,26,35,.95), rgba(16,21,29,.95));
          border: 1px solid var(--border);
          border-radius: 18px;
          padding: 22px;
          box-shadow: 0 18px 40px rgba(0,0,0,.25);
        }}
        h1 {{
          margin: 0 0 12px;
          font-size: 32px;
        }}
        h2 {{
          margin: 0 0 14px;
          font-size: 18px;
        }}
        p {{
          color: var(--muted);
          line-height: 1.5;
        }}
        .cards {{
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
        }}
        .card {{
          background: rgba(255,255,255,.03);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: 14px;
        }}
        .label {{
          color: var(--muted);
          font-size: 13px;
          margin-bottom: 4px;
        }}
        .value {{
          font-size: 28px;
          font-weight: 700;
        }}
        .bar {{
          height: 8px;
          background: rgba(255,255,255,.08);
          border-radius: 999px;
          overflow: hidden;
          margin-top: 10px;
        }}
        .bar span {{
          display: block;
          height: 100%;
          border-radius: inherit;
          background: linear-gradient(90deg, var(--accent), #7af0a8);
        }}
        .trend {{
          margin-top: 8px;
          font-size: 12px;
          color: var(--muted);
        }}
        .trend.up {{
          color: #8cf1b1;
        }}
        .trend.down {{
          color: #ff8a8a;
        }}
        .detail-grid {{
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 14px;
        }}
        .detail-box {{
          background: rgba(255,255,255,.03);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: 14px;
        }}
        .detail-title {{
          color: var(--muted);
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: .04em;
          margin-bottom: 8px;
        }}
        .detail-answer, .detail-context {{
          color: var(--text);
          line-height: 1.55;
          white-space: pre-wrap;
          word-break: break-word;
          font-size: 14px;
        }}
        .detail-actions {{
          display: flex;
          gap: 10px;
          margin-bottom: 10px;
          flex-wrap: wrap;
        }}
        .button {{
          background: rgba(255,255,255,.05);
          border: 1px solid var(--border);
          color: var(--text);
          border-radius: 999px;
          padding: 8px 12px;
          font-size: 13px;
          cursor: pointer;
        }}
        .button:hover {{
          border-color: rgba(55,214,122,.45);
        }}
        .button.primary {{
          background: rgba(55,214,122,.12);
          border-color: rgba(55,214,122,.35);
        }}
        .detail-meta {{
          color: var(--muted);
          font-size: 13px;
          margin-bottom: 10px;
          white-space: pre-line;
          word-break: break-word;
        }}
        .metric-list {{
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px;
          margin-bottom: 10px;
        }}
        .metric-pill {{
          background: rgba(255,255,255,.03);
          border: 1px solid var(--border);
          border-radius: 12px;
          padding: 10px 12px;
        }}
        .metric-name {{
          color: var(--muted);
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: .04em;
        }}
        .metric-value {{
          font-size: 22px;
          font-weight: 700;
          margin-top: 4px;
        }}
        .toolbar {{
          display: flex;
          gap: 12px;
          align-items: center;
          flex-wrap: wrap;
          margin-top: 12px;
        }}
        .search {{
          flex: 1 1 260px;
          min-width: 220px;
          background: rgba(255,255,255,.04);
          border: 1px solid var(--border);
          border-radius: 999px;
          padding: 10px 14px;
          color: var(--text);
          outline: none;
        }}
        .search::placeholder {{
          color: var(--muted);
        }}
        .toggle {{
          display: inline-flex;
          align-items: center;
          gap: 8px;
          color: var(--muted);
          font-size: 13px;
          user-select: none;
        }}
        .toggle input {{
          accent-color: var(--accent);
        }}
        .run-row:hover {{
          background: rgba(255,255,255,.03);
          cursor: pointer;
        }}
        .run-row.active {{
          background: rgba(55, 214, 122, 0.08);
        }}
        .run-row.hidden {{
          display: none;
        }}
        table {{
          width: 100%;
          border-collapse: collapse;
          margin-top: 18px;
          overflow: hidden;
        }}
        th, td {{
          text-align: left;
          padding: 12px 10px;
          border-bottom: 1px solid rgba(255,255,255,.07);
        }}
        th {{
          color: var(--muted);
          font-weight: 600;
          font-size: 13px;
          text-transform: uppercase;
          letter-spacing: .04em;
        }}
        .tag {{
          display: inline-block;
          padding: 4px 10px;
          border: 1px solid rgba(55,214,122,.35);
          color: #8cf1b1;
          border-radius: 999px;
          font-size: 12px;
          margin-bottom: 14px;
        }}
        .small {{
          font-size: 13px;
          color: var(--muted);
        }}
        .legend {{
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          margin-top: 12px;
          font-size: 12px;
          color: var(--muted);
        }}
        .legend span {{
          padding: 4px 8px;
          border: 1px solid var(--border);
          border-radius: 999px;
        }}
        .report-link {{
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }}
        a {{
          color: #8dc7ff;
          text-decoration: none;
        }}
        a:hover {{
          text-decoration: underline;
        }}
        .detail-header {{
          display: flex;
          justify-content: space-between;
          gap: 12px;
          align-items: baseline;
        }}
        @media (max-width: 900px) {{
          .hero {{ grid-template-columns: 1fr; }}
          .detail-grid {{ grid-template-columns: 1fr; }}
        }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="tag">Benchmark Dashboard</div>
        <div class="hero">
          <div class="panel">
            <h1>RAG Benchmark Overview</h1>
            <p>This dashboard summarizes the latest benchmark run and the recent benchmark history for the local RAG pipeline.</p>
            <div class="small">Latest question: {_escape(latest_question)}</div>
            <div class="small">Latest run is saved locally and can be inspected in the detail panel.</div>
            <div class="legend">
              <span>Green means improvement</span>
              <span>Red means regression</span>
              <span>Bars show the current score out of 1.0</span>
            </div>
          </div>
          <div class="panel">
            <h2>Latest Metrics</h2>
            <div class="cards">
              {''.join(cards)}
            </div>
          </div>
        </div>
        <div class="panel" style="margin-top:18px;">
          <h2>Recent Runs</h2>
          <div class="toolbar">
            <input id="run-search" class="search" type="search" placeholder="Filter runs by question..." />
            <label class="toggle">
              <input id="exact-toggle" type="checkbox" />
              Match exact question text
            </label>
          </div>
          <table>
            <thead>
              <tr>
                <th>Question</th>
                <th>Context P</th>
                <th>Answer R</th>
                <th>Faith</th>
                <th>Recall</th>
              </tr>
            </thead>
            <tbody>
              {''.join(rows)}
            </tbody>
          </table>
        </div>
        <div class="panel" style="margin-top:18px;">
          <div class="detail-header">
            <h2>Selected Run</h2>
            <label class="toggle">
              <input id="context-toggle" type="checkbox" checked />
              Show retrieved context
            </label>
          </div>
          <div id="run-detail" class="detail-grid">
            <div class="detail-box">
              <div class="detail-title">Question</div>
              <div id="detail-question" class="detail-answer">{_escape(latest_question)}</div>
            </div>
            <div class="detail-box">
              <div class="detail-title">Metrics</div>
              <div class="metric-list" id="detail-metrics"></div>
              <div class="detail-meta" id="detail-report"></div>
            </div>
            <div class="detail-box">
              <div class="detail-title">Answer</div>
              <div class="detail-actions">
                <button id="copy-answer" class="button" type="button">Copy answer</button>
                <a id="open-report" class="button primary report-link" href="#" target="_blank" rel="noopener">Open full report</a>
                <a id="download-report" class="button report-link" href="#" download>Download HTML</a>
              </div>
              <div id="detail-answer" class="detail-answer">{_escape(latest_answer)}</div>
            </div>
            <div class="detail-box" id="context-box">
              <div class="detail-title">Retrieved Context</div>
              <div id="detail-context" class="detail-context">{_escape(latest_context)}</div>
            </div>
          </div>
        </div>
      </div>
      <script>
        const runs = {json.dumps(detail_payload, ensure_ascii=False)};
        const detailQuestion = document.getElementById("detail-question");
        const detailMetrics = document.getElementById("detail-metrics");
        const detailReport = document.getElementById("detail-report");
        const detailAnswer = document.getElementById("detail-answer");
        const detailContext = document.getElementById("detail-context");
        const contextBox = document.getElementById("context-box");
        const openReport = document.getElementById("open-report");
        const downloadReport = document.getElementById("download-report");
        const runSearch = document.getElementById("run-search");
        const exactToggle = document.getElementById("exact-toggle");
        const contextToggle = document.getElementById("context-toggle");
        const copyAnswer = document.getElementById("copy-answer");
        const rows = document.querySelectorAll(".run-row");
        let activeIndex = 0;

        function renderDetail(run) {{
          detailQuestion.textContent = run.question || "";
          detailAnswer.textContent = run.answer || "No answer saved.";
          detailContext.textContent = run.retrieved_context || "No retrieved context saved.";
          detailMetrics.innerHTML = [
            ["Context precision", Number(run.context_precision || 0).toFixed(3)],
            ["Answer relevancy", Number(run.answer_relevancy || 0).toFixed(3)],
            ["Faithfulness", Number(run.faithfulness || 0).toFixed(3)],
            ["Context recall", Number(run.context_recall || 0).toFixed(3)],
            ["Reference similarity", Number(run.reference_similarity || 0).toFixed(3)]
          ].map(([name, value]) => `
            <div class="metric-pill">
              <div class="metric-name">${{name}}</div>
              <div class="metric-value">${{value}}</div>
            </div>
          `).join("");
          detailReport.textContent = run.timestamp_utc ? `Timestamp: ${{run.timestamp_utc}}` : "";
          if (openReport) {{
            openReport.href = run.report_href ? run.report_href : "#";
            openReport.setAttribute("aria-disabled", run.report_href ? "false" : "true");
            openReport.style.pointerEvents = run.report_href ? "auto" : "none";
            openReport.style.opacity = run.report_href ? "1" : "0.55";
          }}
          if (downloadReport) {{
            downloadReport.href = run.report_href ? run.report_href : "#";
            downloadReport.setAttribute("aria-disabled", run.report_href ? "false" : "true");
            downloadReport.style.pointerEvents = run.report_href ? "auto" : "none";
            downloadReport.style.opacity = run.report_href ? "1" : "0.55";
          }}
        }}

        function setActiveRow(index) {{
          activeIndex = index;
          rows.forEach((row) => {{
            row.classList.toggle("active", Number(row.dataset.index) === index);
          }});
        }}

        function applyFilter() {{
          const query = (runSearch.value || "").trim().toLowerCase();
          const exact = exactToggle.checked;
          rows.forEach((row) => {{
            const run = runs[Number(row.dataset.index)];
            const question = (run && run.question) ? run.question.toLowerCase() : "";
            const match = !query || (exact ? question === query : question.includes(query));
            row.classList.toggle("hidden", !match);
          }});
        }}

        rows.forEach((row) => {{
          row.addEventListener("click", () => {{
            const run = runs[Number(row.dataset.index)];
            if (run) {{
              renderDetail(run);
              setActiveRow(Number(row.dataset.index));
            }}
          }});
        }});

        copyAnswer.addEventListener("click", async () => {{
          const text = detailAnswer.textContent || "";
          if (!text) {{
            return;
          }}
          try {{
            await navigator.clipboard.writeText(text);
            copyAnswer.textContent = "Copied";
            setTimeout(() => {{ copyAnswer.textContent = "Copy answer"; }}, 1200);
          }} catch (error) {{
            copyAnswer.textContent = "Copy failed";
            setTimeout(() => {{ copyAnswer.textContent = "Copy answer"; }}, 1200);
          }}
        }});

        runSearch.addEventListener("input", applyFilter);
        exactToggle.addEventListener("change", applyFilter);
        contextToggle.addEventListener("change", () => {{
          contextBox.style.display = contextToggle.checked ? "" : "none";
        }});

        renderDetail(runs[0] || {json.dumps(initial_detail, ensure_ascii=False)});
        setActiveRow(0);
        applyFilter();
        contextToggle.dispatchEvent(new Event("change"));
      </script>
    </body>
    </html>
    """
    return html.strip()


def save_dashboard_html(reports_dir: Path = reports_root(), output_path: Path | None = None, limit: int = 10) -> Path:
    output_path = output_path or (reports_dir / "benchmark_dashboard.html")
    output_path.write_text(build_dashboard_html(reports_dir=reports_dir, limit=limit), encoding="utf-8")
    return output_path


def build_report_page_html(report_path: Path) -> str:
    details = _load_report_details(str(report_path))
    title = details.get("question") or report_path.stem
    metrics = [
        ("Context Precision", details.get("context_precision", 0.0)),
        ("Answer Relevancy", details.get("answer_relevancy", 0.0)),
        ("Faithfulness", details.get("faithfulness", 0.0)),
        ("Context Recall", details.get("context_recall", 0.0)),
        ("Reference Similarity", details.get("reference_similarity", 0.0)),
    ]
    answer_text = str(details.get("answer", "") or "")
    source_count = 0
    if details.get("retrieved_context"):
        source_count = len([chunk for chunk in str(details.get("retrieved_context", "")).split("\n\n") if chunk.strip()])
    metrics_html = "".join(
        f"""
        <div class="metric-card">
          <div class="metric-name">{_escape(label)}</div>
          <div class="metric-value">{float(value):.4f}</div>
          {_metric_bar(float(value))}
        </div>
        """
        for label, value in metrics
    )
    report_html_name = _report_page_name(str(report_path))
    top_metric = max(metrics, key=lambda item: item[1])[0] if metrics else "N/A"
    return f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{_escape(title)} - RAG Report</title>
      <style>
        :root {{
          color-scheme: dark;
          --bg: #0e1117;
          --panel: #151a23;
          --text: #e6edf3;
          --muted: #9aa4b2;
          --accent: #37d67a;
          --border: #243041;
        }}
        body {{
          margin: 0;
          font-family: Segoe UI, Arial, sans-serif;
          background: radial-gradient(circle at top, #172033, var(--bg) 55%);
          color: var(--text);
        }}
        .wrap {{
          max-width: 1080px;
          margin: 0 auto;
          padding: 32px 20px 48px;
        }}
        .panel {{
          background: linear-gradient(180deg, rgba(21,26,35,.95), rgba(16,21,29,.95));
          border: 1px solid var(--border);
          border-radius: 18px;
          padding: 22px;
          box-shadow: 0 18px 40px rgba(0,0,0,.25);
        }}
        .hero-panel {{
          display: grid;
          grid-template-columns: 1.6fr .9fr;
          gap: 18px;
          align-items: start;
        }}
        h1 {{
          margin: 0 0 12px;
          font-size: 30px;
        }}
        h2 {{
          margin: 0 0 14px;
          font-size: 18px;
        }}
        p {{
          color: var(--muted);
          line-height: 1.55;
          white-space: pre-wrap;
        }}
        .header {{
          display: flex;
          justify-content: space-between;
          gap: 16px;
          align-items: start;
          flex-wrap: wrap;
        }}
        .nav {{
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin-top: 14px;
        }}
        .nav a {{
          color: var(--muted);
          text-decoration: none;
          padding: 6px 10px;
          border-radius: 999px;
          border: 1px solid var(--border);
          background: rgba(255,255,255,.02);
          font-size: 12px;
        }}
        .tag {{
          display: inline-block;
          padding: 4px 10px;
          border: 1px solid rgba(55,214,122,.35);
          color: #8cf1b1;
          border-radius: 999px;
          font-size: 12px;
          margin-bottom: 14px;
        }}
        .metrics {{
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
        }}
        .metric-card {{
          background: rgba(255,255,255,.03);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: 14px;
        }}
        .metric-name {{
          color: var(--muted);
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: .04em;
        }}
        .metric-value {{
          margin-top: 6px;
          font-size: 28px;
          font-weight: 700;
        }}
        .bar {{
          height: 8px;
          background: rgba(255,255,255,.08);
          border-radius: 999px;
          overflow: hidden;
          margin-top: 10px;
        }}
        .bar span {{
          display: block;
          height: 100%;
          border-radius: inherit;
          background: linear-gradient(90deg, var(--accent), #7af0a8);
        }}
        .section {{
          margin-top: 18px;
        }}
        .box {{
          background: rgba(255,255,255,.03);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: 16px;
        }}
        .meta {{
          color: var(--muted);
          font-size: 13px;
          margin-top: 8px;
          white-space: pre-wrap;
          word-break: break-word;
        }}
        .context {{
          white-space: pre-wrap;
          line-height: 1.6;
          word-break: break-word;
          font-size: 14px;
        }}
        .actions {{
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin-top: 12px;
        }}
        .button {{
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 9px 14px;
          border-radius: 999px;
          background: rgba(255,255,255,.05);
          border: 1px solid var(--border);
          color: var(--text);
          text-decoration: none;
        }}
        .button.primary {{
          background: rgba(55,214,122,.12);
          border-color: rgba(55,214,122,.35);
        }}
        .small {{
          color: var(--muted);
          font-size: 13px;
        }}
        .chips {{
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin-top: 16px;
        }}
        .chip {{
          padding: 8px 10px;
          border-radius: 999px;
          border: 1px solid var(--border);
          background: rgba(255,255,255,.03);
          font-size: 12px;
          color: var(--muted);
        }}
        .hero-aside {{
          display: grid;
          gap: 10px;
        }}
        .hero-stat {{
          background: rgba(255,255,255,.03);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: 14px;
        }}
        .hero-stat .metric-name {{
          font-size: 11px;
        }}
        .hero-stat .metric-value {{
          font-size: 24px;
        }}
        .summary-strip {{
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
          margin-top: 18px;
        }}
        .summary-item {{
          background: rgba(255,255,255,.03);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: 14px;
        }}
        .summary-item .metric-name {{
          font-size: 11px;
        }}
        .summary-item .metric-value {{
          font-size: 22px;
        }}
        @media (max-width: 800px) {{
          .metrics {{
            grid-template-columns: 1fr;
          }}
          .hero-panel {{
            grid-template-columns: 1fr;
          }}
          .summary-strip {{
            grid-template-columns: 1fr;
          }}
        }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="tag">Run Report</div>
        <div class="panel hero-panel">
          <div class="header">
            <div>
              <h1>{_escape(title)}</h1>
              <div class="small">A single benchmark run with answer, metrics, and retrieved context.</div>
              <div class="chips">
                <span class="chip">Answer quality</span>
                <span class="chip">Retrieval evidence</span>
                <span class="chip">Metric history</span>
              </div>
              <div class="nav">
                <a href="#metrics">Metrics</a>
                <a href="#answer">Answer</a>
                <a href="#context">Retrieved context</a>
              </div>
              <div class="meta">{_escape(details.get("timestamp_utc", ""))}</div>
            </div>
            <div class="actions">
              <a class="button" href="../benchmark_dashboard.html">Back to dashboard</a>
              <a class="button primary" href="{_escape(report_html_name)}" download>Download HTML</a>
            </div>
          </div>
          <div class="hero-aside">
            <div class="hero-stat">
              <div class="metric-name">Question</div>
              <div class="metric-value">{_escape(title)}</div>
            </div>
            <div class="hero-stat">
              <div class="metric-name">Report file</div>
              <div class="metric-value">{_escape(report_html_name)}</div>
            </div>
          </div>
        </div>
        <div class="summary-strip">
          <div class="summary-item">
            <div class="metric-name">Answer preview</div>
            <div class="metric-value">{_escape(answer_text[:48] + ("..." if len(answer_text) > 48 else ""))}</div>
          </div>
          <div class="summary-item">
            <div class="metric-name">Retrieved sources</div>
            <div class="metric-value">{source_count}</div>
          </div>
          <div class="summary-item">
            <div class="metric-name">Top metric</div>
            <div class="metric-value">{_escape(top_metric)}</div>
          </div>
        </div>
        <div class="section panel">
          <h2 id="metrics">Metrics</h2>
          <div class="metrics">{metrics_html}</div>
        </div>
        <div class="section panel">
          <h2 id="answer">Answer</h2>
          <div class="box">
            <div class="context">{_escape(answer_text)}</div>
          </div>
        </div>
        <div class="section panel">
          <h2 id="context">Retrieved Context</h2>
          <div class="box">
            <div class="context">{_escape(details.get("retrieved_context", "")) or "No retrieved context saved."}</div>
          </div>
        </div>
      </div>
    </body>
    </html>
    """.strip()


def save_report_pages(reports_dir: Path = reports_root(), limit: int = 10) -> list[Path]:
    index = build_history_index(reports_dir)
    output_dir = reports_dir / "report-pages"
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for run in index.get("runs", [])[:limit]:
        report_path = Path(run["report_path"])
        page_path = output_dir / _report_page_name(str(report_path))
        page_path.write_text(build_report_page_html(report_path), encoding="utf-8")
        written.append(page_path)
    return written
