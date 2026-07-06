from __future__ import annotations

import html
import os
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from email.parser import BytesParser
from email.policy import default as email_default_policy
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from rag_pipeline.auth import authenticate_user, bootstrap_admin_from_env, create_token, generate_otp, register_user, reset_admin_password_from_env, verify_otp, verify_token
from rag_pipeline.auth import delete_question_history, load_question_history, save_question_history
from rag_pipeline.cli import run_cli
from rag_pipeline.env import load_dotenv
from rag_pipeline.benchmark_history import load_latest_answers
from rag_pipeline.uploads import (
    approve_upload,
    approved_input_dir,
    list_approved_files,
    list_uploads,
    list_user_uploads,
    reject_upload,
    upload_file_type_breakdown,
    save_pending_upload,
)

logger = logging.getLogger(__name__)


def _cookie_value(cookie_header: str | None, key: str) -> str:
    if not cookie_header:
        return ""
    for part in cookie_header.split(";"):
        name, _, value = part.strip().partition("=")
        if name == key:
            return value
    return ""


def _escape(text: object) -> str:
    return html.escape(str(text), quote=True)


def _send_json(handler: BaseHTTPRequestHandler, payload: dict[str, object], status: int = 200) -> None:
    data = __import__("json").dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _user_key(user: dict[str, object]) -> str:
    return str(user.get("email") or user.get("username") or "")


def _read_request_body(handler: BaseHTTPRequestHandler) -> bytes:
    length = int(handler.headers.get("Content-Length", "0") or 0)
    return handler.rfile.read(length) if length > 0 else b""


def _parse_form_fields(handler: BaseHTTPRequestHandler) -> tuple[dict[str, str], list[tuple[str, str, bytes]]]:
    content_type = handler.headers.get("Content-Type", "")
    body = _read_request_body(handler)
    fields: dict[str, str] = {}
    files: list[tuple[str, str, bytes]] = []
    if "multipart/form-data" in content_type:
        header_bytes = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
        message = BytesParser(policy=email_default_policy).parsebytes(header_bytes + body)
        for part in message.iter_parts():
            disposition = part.get("Content-Disposition", "")
            name = part.get_param("name", header="content-disposition") or ""
            filename = part.get_filename() or ""
            payload = part.get_payload(decode=True) or b""
            if filename:
                files.append((name, filename, payload))
            elif name:
                fields[name] = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        return fields, files
    parsed = parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True)
    for key, value in parsed.items():
        fields[key] = value[0] if value else ""
    return fields, files


def _render_result(result: dict[str, object] | None = None, error: str = "", user: dict[str, object] | None = None) -> str:
    question = str((result or {}).get("question", ""))
    answer = str((result or {}).get("answer", ""))
    why_answer = str((result or {}).get("why_answer", ""))
    report_path = str((result or {}).get("report_path", ""))
    report_href = report_path if report_path else ""
    citations = list((result or {}).get("citations", []))
    is_signed_in = bool(user)
    auth_badge = ""
    auth_links = """
        <a class="button" href="/login">Login</a>
        <a class="button" href="/register">Register</a>
        <a class="button" href="/verify-otp">Verify OTP</a>
        <a class="button" href="/admin/login">Admin login</a>
    """
    if user:
        auth_badge = f"<span class='chip'>{_escape(user.get('role', 'user'))}</span><span class='chip'>{_escape(user.get('username', user.get('email', '')))}</span>"
        auth_links = """
            <a class="button" href="/dashboard">Dashboard</a>
            <a class="button" href="/logout">Logout</a>
        """
    documents = result.get("documents", 0) if result else 0
    chunks = result.get("chunks", 0) if result else 0
    retrieval_results = result.get("retrieval_results", 0) if result else 0
    metrics = [
        ("Context precision", result.get("context_precision", 0.0) if result else 0.0),
        ("Answer relevancy", result.get("answer_relevancy", 0.0) if result else 0.0),
        ("Faithfulness", result.get("faithfulness", 0.0) if result else 0.0),
        ("Context recall", result.get("context_recall", 0.0) if result else 0.0),
    ]
    metric_cards = "".join(
        f"""
        <div class="metric">
          <div class="metric-label">{_escape(label)}</div>
          <div class="metric-value">{float(value):.4f}</div>
        </div>
        """
        for label, value in metrics
    )
    citation_cards = "".join(
        f"""
        <div class="box">
          <div class="metric-label">Source {index}</div>
          <div class="metric-value" style="font-size:16px;line-height:1.35;">{_escape(item.get('source_path', ''))}</div>
          <div class="small" style="margin-top:8px;">Score: {_escape(f"{float(item.get('score', 0.0)):.4f}")} | Chunk: {_escape(item.get('chunk_id', ''))}</div>
          <div class="small" style="margin-top:8px;">{_escape(item.get('preview', ''))}</div>
        </div>
        """
        for index, item in enumerate(citations, start=1)
    ) or "<div class='box'><div class='small'>No citations available for this answer.</div></div>"
    result_summary = "".join(
        f"""
        <div class="box">
          <div class="metric-label">{_escape(label)}</div>
          <div class="metric-value">{_escape(value)}</div>
        </div>
        """
        for label, value in [
            ("Documents", documents),
            ("Chunks", chunks),
            ("Retrieved", retrieval_results),
        ]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RAG Upload Demo</title>
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
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .panel {{
      background: linear-gradient(180deg, rgba(21,26,35,.95), rgba(16,21,29,.95));
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 18px 40px rgba(0,0,0,.25);
      margin-bottom: 18px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.2fr .8fr;
      gap: 18px;
    }}
    h1 {{ margin: 0 0 12px; font-size: 32px; }}
    h2 {{ margin: 0 0 14px; font-size: 18px; }}
    p {{ color: var(--muted); line-height: 1.55; }}
    .form-grid {{
      display: grid;
      gap: 12px;
      margin-top: 14px;
    }}
    .input, textarea {{
      width: 100%;
      box-sizing: border-box;
      background: rgba(255,255,255,.04);
      border: 1px solid var(--border);
      border-radius: 14px;
      color: var(--text);
      padding: 12px 14px;
      font: inherit;
    }}
    textarea {{ min-height: 100px; resize: vertical; }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,.05);
      color: var(--text);
      cursor: pointer;
      text-decoration: none;
      font: inherit;
    }}
    .button.primary {{
      background: rgba(55,214,122,.12);
      border-color: rgba(55,214,122,.35);
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }}
    .metric {{
      background: rgba(255,255,255,.03);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px 14px;
    }}
    .metric-label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .04em;
    }}
    .metric-value {{
      margin-top: 6px;
      font-size: 22px;
      font-weight: 700;
    }}
    .result-summary {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .stack {{
      display: grid;
      gap: 18px;
      margin-top: 18px;
    }}
    .citations {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}
    .box {{
      background: rgba(255,255,255,.03);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
    }}
    .context {{
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.55;
      font-size: 14px;
    }}
    .small {{
      color: var(--muted);
      font-size: 13px;
      word-break: break-word;
    }}
    .error {{
      color: #ff8a8a;
      margin-top: 10px;
    }}
    .summary {{
      display: none;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,.03);
      color: var(--muted);
      font-size: 12px;
      margin-right: 8px;
      margin-bottom: 8px;
    }}
    .auth-row {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 12px;
    }}
    .metric-note {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
      margin-top: 10px;
    }}
    .approved-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .approved-grid .box {{
      padding: 14px;
    }}
    @media (max-width: 900px) {{
      .hero, .metrics, .result-summary, .citations {{
        grid-template-columns: 1fr;
      }}
      .approved-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <h2>Account</h2>
      <div class="small">{'Signed in as' if is_signed_in else 'Not signed in'}: {auth_badge or "<span class='chip'>Guest</span>"}</div>
      <div class="auth-row">
        {auth_links}
      </div>
    </div>
    <div class="panel">
      <h2>RAG metrics explained</h2>
      <p class="small">These metrics help you understand not just the answer itself, but how well the system found evidence, stayed on topic, and remained grounded in the source documents.</p>
      <div class="metrics">
        <div class="metric">
          <div class="metric-label">Context precision</div>
          <div class="metric-value" style="font-size:16px;line-height:1.35;">How clean the retrieved sources are. High precision means the system found mostly useful passages instead of noisy ones.</div>
          <div class="small" style="margin-top:10px;">Why it matters: better source quality usually means the answer is less distracted by irrelevant text.</div>
        </div>
        <div class="metric">
          <div class="metric-label">Answer relevancy</div>
          <div class="metric-value" style="font-size:16px;line-height:1.35;">How well the final answer matches the question asked. It checks whether the response stays on-topic.</div>
          <div class="small" style="margin-top:10px;">Why it matters: users want answers that directly solve their question, not just related text.</div>
        </div>
        <div class="metric">
          <div class="metric-label">Faithfulness</div>
          <div class="metric-value" style="font-size:16px;line-height:1.35;">How well the answer stays grounded in the retrieved context. High faithfulness means the model is not inventing unsupported details.</div>
          <div class="small" style="margin-top:10px;">Why it matters: this is what keeps the answer trustworthy.</div>
        </div>
        <div class="metric">
          <div class="metric-label">Context recall</div>
          <div class="metric-value" style="font-size:16px;line-height:1.35;">How much of the useful evidence the retriever managed to pull in. Higher recall means more of the important material was captured.</div>
          <div class="small" style="margin-top:10px;">Why it matters: if recall is too low, the model may miss the key facts it needs.</div>
        </div>
      </div>
    </div>
    <div class="panel hero">
      <div>
        <h1>Upload, approve, then ask</h1>
        <p>Files first go into a pending queue. An admin approves them into permanent storage, and only then do they become part of the searchable corpus for the question flow.</p>
        <form class="form-grid" action="/submit-upload" method="post" enctype="multipart/form-data">
          <input class="input" type="text" name="upload_title" placeholder="Upload title or label" required>
          <input class="input" type="file" name="files" multiple required>
          <textarea name="notes" placeholder="Optional admin notes."></textarea>
          <div>
            <button class="button primary" type="submit">Submit for approval</button>
          </div>
        </form>
      </div>
      <div class="box">
        <h2>How it works</h2>
        <p>1. Upload files into pending storage.</p>
        <p>2. Admin approves or rejects them from the admin page.</p>
        <p>3. Ask questions only against the approved corpus.</p>
        <div style="margin-top:12px;">
          <a class="button" href="/admin">Open admin queue</a>
        </div>
      </div>
    </div>
    <div class="panel">
      <h2>Ask a question</h2>
      <p class="small">This runs against the approved permanent storage, not the pending uploads.</p>
      <form class="form-grid" action="/ask" method="post">
        <input class="input" type="text" name="question" placeholder="Ask about your approved files..." required value="{_escape(question)}">
        <div>
          <button class="button primary" type="submit">Run RAG pipeline</button>
        </div>
      </form>
      {f'<div class="error">{_escape(error)}</div>' if error else ''}
      </div>
    {f'''
    <div class="stack">
      <div class="panel">
        <h2>Run summary</h2>
        <div class="result-summary">{result_summary}</div>
      </div>
      <div class="panel">
        <h2>Metrics</h2>
        <div class="metrics">{metric_cards}</div>
      </div>
      <div class="panel">
        <h2>Answer</h2>
        <div class="box"><div class="context">{_escape(answer[:420])}{'…' if len(answer) > 420 else ''}</div></div>
      </div>
      <div class="panel">
        <h2>Source citations</h2>
        <p class="small">These are the source snippets the answer was grounded in, so users can verify the response quickly.</p>
        <div class="citations">{citation_cards}</div>
      </div>
      <div class="panel">
        <h2>Why this answer</h2>
        <div class="box"><div class="context">{_escape(why_answer) or "The answer was grounded in the retrieved context and the top-ranked chunks."}</div></div>
      </div>
      <div class="panel">
        <h2>Saved report</h2>
        <div class="small">{_escape(report_path)}</div>
        <div style="margin-top:12px;">
          <a class="button" href="/download?path={_escape(report_path)}">Download JSON report</a>
          {f'<a class="button" href="{_escape(report_href)}" download>Download HTML report</a>' if report_href else ''}
        </div>
      </div>
    </div>
    ''' if result else ''}
  </div>
</body>
</html>"""


def _render_admin(search: str = "") -> str:
    pending = list_uploads("pending")
    approved = list_uploads("approved")
    rejected = list_uploads("rejected")
    recent_answers = load_latest_answers(limit=5)
    pending_file_types = upload_file_type_breakdown("pending")
    approved_file_types = upload_file_type_breakdown("approved")
    search_lower = search.lower().strip()
    if search_lower:
        def _matches(item: dict[str, object]) -> bool:
            return any(
                search_lower in str(item.get(field, "")).lower()
                for field in ("upload_id", "question", "notes", "review_note", "path")
            ) or any(search_lower in str(name).lower() for name in item.get("files", []))

        pending = [item for item in pending if _matches(item)]
        approved = [item for item in approved if _matches(item)]
        rejected = [item for item in rejected if _matches(item)]
        recent_answers = [
            item
            for item in recent_answers
            if search_lower in str(item.get("question", "")).lower()
            or search_lower in str(item.get("answer", "")).lower()
        ]
    pending_rows = "".join(
        f"""
        <tr>
          <td>{_escape(item.get("upload_id", ""))}</td>
          <td>{_escape(item.get("question", ""))}</td>
          <td>{_escape(", ".join(item.get("files", [])))}</td>
          <td>{_escape(item.get("notes", ""))}</td>
          <td>
            <form id="action-{_escape(item.get('upload_id', ''))}" method="get" action="/admin/action" style="display:inline-flex;gap:8px;align-items:center;flex-wrap:wrap;">
              <input type="hidden" name="id" value="{_escape(item.get('upload_id', ''))}">
              <input class="input" name="review_note" placeholder="Review note" style="width:220px;">
              <button class="button" type="submit" name="decision" value="approve">Approve</button>
              <button class="button" type="submit" name="decision" value="reject">Reject</button>
            </form>
          </td>
        </tr>
        """
        for item in pending
    ) or "<tr><td colspan='5'>No pending uploads.</td></tr>"
    approved_cards = "".join(
        f"""<div class="mini-card"><strong>{_escape(item.get("upload_id", ""))}</strong><div>{_escape(item.get("question", ""))}</div></div>"""
        for item in approved[:3]
    ) or "<div class='mini-card'>No approved uploads yet.</div>"
    rejected_cards = "".join(
        f"""<div class="mini-card"><strong>{_escape(item.get("upload_id", ""))}</strong><div>{_escape(item.get("question", ""))}</div></div>"""
        for item in rejected[:3]
    ) or "<div class='mini-card'>No rejected uploads yet.</div>"
    recent_answer_cards = "".join(
        f"""
        <div class="mini-card">
          <div class="metric">Question</div>
          <div><strong>{_escape(item.get("question", ""))}</strong></div>
          <div class="small" style="margin-top:8px;">Answer: {_escape(str(item.get("answer", ""))[:160])}</div>
          <div class="small">Report: {_escape(item.get("report_path", ""))}</div>
        </div>
        """
        for item in recent_answers
    ) or "<div class='mini-card'>No saved answers yet.</div>"
    pending_type_cards = "".join(
        f"""<div class="mini-card"><div class="metric">{_escape(item.get("file_type", ""))}</div><div class="value">{_escape(item.get("count", 0))}</div></div>"""
        for item in pending_file_types
    ) or "<div class='mini-card'>No pending file types yet.</div>"
    approved_type_cards = "".join(
        f"""<div class="mini-card"><div class="metric">{_escape(item.get("file_type", ""))}</div><div class="value">{_escape(item.get("count", 0))}</div></div>"""
        for item in approved_file_types
    ) or "<div class='mini-card'>No approved file types yet.</div>"
    pending_max = max((int(item.get("count", 0)) for item in pending_file_types), default=1)
    approved_max = max((int(item.get("count", 0)) for item in approved_file_types), default=1)
    palette = ["#37d67a", "#4aa3ff", "#a78bfa", "#f59e0b", "#f43f5e", "#14b8a6", "#eab308"]

    def _file_type_color(label: str) -> str:
        if not label:
            return palette[0]
        index = sum(ord(ch) for ch in label.lower()) % len(palette)
        return palette[index]

    pending_bars = "".join(
        f"""
        <div class="bar-row">
          <div class="bar-label">{_escape(item.get("file_type", ""))}</div>
          <div class="bar-track"><div class="bar-fill" style="width:{(int(item.get('count', 0)) / pending_max * 100) if pending_max else 0:.0f}%;background:linear-gradient(90deg,{_file_type_color(str(item.get('file_type', '')))},#4aa3ff)"></div></div>
          <div class="bar-count">{_escape(item.get("count", 0))}</div>
        </div>
        """
        for item in pending_file_types
    ) or "<div class='small'>No pending file types yet.</div>"
    approved_bars = "".join(
        f"""
        <div class="bar-row">
          <div class="bar-label">{_escape(item.get("file_type", ""))}</div>
          <div class="bar-track"><div class="bar-fill" style="width:{(int(item.get('count', 0)) / approved_max * 100) if approved_max else 0:.0f}%;background:linear-gradient(90deg,{_file_type_color(str(item.get('file_type', '')))},#4aa3ff)"></div></div>
          <div class="bar-count">{_escape(item.get("count", 0))}</div>
        </div>
        """
        for item in approved_file_types
    ) or "<div class='small'>No approved file types yet.</div>"
    all_types = {str(item.get("file_type", "")) for item in pending_file_types + approved_file_types}
    legend_items = "".join(
        f"""<span class="legend-item"><span class="legend-dot" style="background:{_file_type_color(label)}"></span>{_escape(label)}</span>"""
        for label in sorted(all_types)[:8]
    ) or "<span class='small'>No file types yet.</span>"
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Admin Queue</title>
<style>
body{{margin:0;font-family:Segoe UI,Arial,sans-serif;background:radial-gradient(circle at top,#172033,#0e1117 55%);color:#e6edf3}}
.wrap{{max-width:1240px;margin:0 auto;padding:32px 20px}}
.panel{{background:linear-gradient(180deg,rgba(21,26,35,.96),rgba(16,21,29,.96));border:1px solid #243041;border-radius:18px;padding:22px;margin-bottom:18px;box-shadow:0 18px 40px rgba(0,0,0,.25)}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:10px;border-bottom:1px solid #243041;text-align:left;vertical-align:top}}
th{{color:#9aa4b2;font-size:12px;text-transform:uppercase;letter-spacing:.05em}}
.button{{display:inline-flex;align-items:center;justify-content:center;padding:10px 14px;border-radius:999px;background:#1b2230;border:1px solid #243041;color:#e6edf3;text-decoration:none;margin-right:8px}}
.mini-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}
.mini-card{{background:rgba(255,255,255,.03);border:1px solid #243041;border-radius:14px;padding:12px}}
.metric{{font-size:12px;color:#9aa4b2;text-transform:uppercase;letter-spacing:.04em}}
.value{{font-size:24px;font-weight:700;margin-top:6px}}
.split{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.topline{{display:flex;justify-content:space-between;gap:14px;align-items:center;flex-wrap:wrap}}
.muted{{color:#9aa4b2;font-size:13px;line-height:1.55}}
.status{{display:inline-flex;align-items:center;padding:5px 10px;border-radius:999px;border:1px solid #243041;background:rgba(255,255,255,.03);font-size:12px;color:#9aa4b2;margin-right:8px}}
.bars{{display:grid;gap:10px;margin-top:10px}}
.bar-row{{display:grid;grid-template-columns:90px 1fr 36px;gap:10px;align-items:center}}
.bar-label{{font-size:12px;color:#9aa4b2;text-transform:uppercase;letter-spacing:.04em}}
.bar-track{{height:12px;background:rgba(255,255,255,.05);border:1px solid #243041;border-radius:999px;overflow:hidden}}
.bar-fill{{height:100%;background:linear-gradient(90deg,#37d67a,#4aa3ff)}}
.bar-count{{font-size:13px;color:#e6edf3;text-align:right}}
.legend{{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}}
.legend-item{{display:inline-flex;align-items:center;gap:8px;color:#c7d0db;font-size:12px;padding:6px 10px;border:1px solid #243041;border-radius:999px;background:rgba(255,255,255,.03)}}
.legend-dot{{width:10px;height:10px;border-radius:999px;display:inline-block}}
@media (max-width:900px){{.mini-grid{{grid-template-columns:1fr}}}}
@media (max-width:900px){{.split{{grid-template-columns:1fr}}}}
</style></head>
<body><div class="wrap">
<div class="panel">
  <div class="topline">
    <div>
      <h1>Admin upload queue</h1>
      <p class="muted">Approve uploads to move them into permanent approved storage.</p>
    </div>
    <div>
      <a class="button" href="/">Back to public page</a>
      <a class="button" href="/dashboard">User dashboard</a>
    </div>
  </div>
  <div style="margin-top:10px;">
    <span class="status">Moderation</span>
    <span class="status">Permanent storage</span>
    <span class="status">Recent answers</span>
  </div>
  <form class="form-grid" method="get" action="/admin" style="margin-top:14px;max-width:520px;">
    <input class="input" type="text" name="q" placeholder="Filter uploads, reviews, or questions..." value="{_escape(search)}">
    <div><button class="button primary" type="submit">Search admin queue</button></div>
  </form>
</div>
<div class="panel">
  <h2>File type breakdown</h2>
  <div class="legend">{legend_items}</div>
  <div class="split">
    <div>
      <h3>Pending file types</h3>
      <div class="bars">{pending_bars}</div>
    </div>
    <div>
      <h3>Approved file types</h3>
      <div class="bars">{approved_bars}</div>
    </div>
  </div>
</div>
<div class="panel"><div class="mini-grid"><div class="mini-card"><div class="metric">Pending</div><div class="value">{len(pending)}</div></div><div class="mini-card"><div class="metric">Approved</div><div class="value">{len(approved)}</div></div><div class="mini-card"><div class="metric">Rejected</div><div class="value">{len(rejected)}</div></div></div></div>
<div class="panel"><h2>Pending uploads</h2><table><thead><tr><th>ID</th><th>Question</th><th>Files</th><th>Notes</th><th>Actions</th></tr></thead><tbody>{pending_rows}</tbody></table></div>
<div class="panel"><h2>Review summary</h2><div class="split"><div><h3>Approved recent</h3><div class="mini-grid">{approved_cards}</div></div><div><h3>Rejected recent</h3><div class="mini-grid">{rejected_cards}</div></div></div></div>
<div class="panel"><h2>Recent answered questions</h2><div class="mini-grid">{recent_answer_cards}</div></div>
</div></body></html>"""


def _render_auth_page(title: str, action: str, fields: list[str], button_label: str, error: str = "") -> str:
    inputs = []
    for field in fields:
        input_type = "password" if field == "password" else "email" if field == "email" else "text"
        inputs.append(f'<input class="input" name="{_escape(field)}" type="{input_type}" placeholder="{_escape(field.title())}">')
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_escape(title)}</title>
<style>
body{{margin:0;font-family:Segoe UI,Arial,sans-serif;background:#0e1117;color:#e6edf3}}
.wrap{{max-width:720px;margin:0 auto;padding:32px 20px}}
.panel{{background:linear-gradient(180deg,rgba(21,26,35,.95),rgba(16,21,29,.95));border:1px solid #243041;border-radius:18px;padding:22px;box-shadow:0 18px 40px rgba(0,0,0,.25)}}
.form-grid{{display:grid;gap:12px;margin-top:14px}}
.input{{width:100%;box-sizing:border-box;background:rgba(255,255,255,.04);border:1px solid #243041;border-radius:14px;color:#e6edf3;padding:12px 14px;font:inherit}}
.button{{display:inline-flex;align-items:center;justify-content:center;padding:10px 14px;border-radius:999px;border:1px solid #243041;background:rgba(255,255,255,.05);color:#e6edf3;text-decoration:none;font:inherit;cursor:pointer}}
.button.primary{{background:rgba(55,214,122,.12);border-color:rgba(55,214,122,.35)}}
.small{{color:#9aa4b2;font-size:13px}}
.error{{color:#ff8a8a;margin-top:10px}}
</style></head>
<body><div class="wrap"><div class="panel"><h1>{_escape(title)}</h1><p class="small">Use this screen to register, verify OTP, or sign in.</p><form class="form-grid" method="post" action="{_escape(action)}">{''.join(inputs)}<button class="button primary" type="submit">{_escape(button_label)}</button></form>{f'<div class="error">{_escape(error)}</div>' if error else ''}<div style="margin-top:12px;"><a class="button" href="/">Back</a></div></div></div></body></html>"""


def _render_user_dashboard(user: dict[str, object], search: str = "") -> str:
    user_key = _user_key(user)
    my_pending = list_user_uploads("pending", user_key)
    my_approved = list_user_uploads("approved", user_key)
    recent_answers = load_question_history(limit=8, user_key=_user_key(user))
    search_lower = search.lower().strip()
    if search_lower:
        my_pending = [
            item
            for item in my_pending
            if search_lower in str(item.get("file_name", "")).lower()
            or search_lower in str(item.get("question", "")).lower()
            or search_lower in str(item.get("path", "")).lower()
        ]
        my_approved = [
            item
            for item in my_approved
            if search_lower in str(item.get("file_name", "")).lower()
            or search_lower in str(item.get("question", "")).lower()
            or search_lower in str(item.get("path", "")).lower()
        ]
        recent_answers = [
            item
            for item in recent_answers
            if search_lower in str(item.get("question", "")).lower()
            or search_lower in str(item.get("answer", "")).lower()
        ]
    my_upload_cards = "".join(
        f"""
        <div class='box file-card'>
          <div class='file-label'>{_escape(item.get('status', 'upload'))}</div>
          <div class='file-title'>{_escape(item.get('file_name', ''))}</div>
          <div class='file-subtitle'>{_escape(item.get('question', ''))}</div>
        </div>
        """
        for item in (my_pending + my_approved)[:6]
    ) or "<div class='box'><div class='small'>No uploads from your account yet.</div></div>"
    recent_answers_html = "".join(
        f"""
        <div class="box">
          <div class="metric">Recent question</div>
          <div class="value" style="font-size:18px;">{_escape(item.get("question", ""))}</div>
          <div class="small" style="margin-top:8px;">Answer: {_escape(str(item.get("answer", ""))[:180])}</div>
          <div class="small">Context precision: {_escape(f'{float(item.get("context_precision", 0.0)):.3f}')}</div>
          <div class="small">Answer relevancy: {_escape(f'{float(item.get("answer_relevancy", 0.0)):.3f}')}</div>
          <div class="small">Faithfulness: {_escape(f'{float(item.get("faithfulness", 0.0)):.3f}')}</div>
          <div style="margin-top:10px;">
            <a class="button" href="/dashboard/delete?report_path={_escape(item.get('report_path', ''))}&q={_escape(search)}">Delete</a>
          </div>
        </div>
        """
        for item in recent_answers[:3]
    ) or "<div class='box'><div class='small'>No answered questions yet.</div></div>"
    history_cards = "".join(
        f"""
        <div class="box">
          <div class="file-label">Evaluation history</div>
          <div class="file-title">{_escape(item.get('question', ''))}</div>
          <div class="history-metrics">
            <div><span>Precision</span><strong>{_escape(f'{float(item.get("context_precision", 0.0)):.3f}')}</strong></div>
            <div><span>Relevancy</span><strong>{_escape(f'{float(item.get("answer_relevancy", 0.0)):.3f}')}</strong></div>
            <div><span>Faithfulness</span><strong>{_escape(f'{float(item.get("faithfulness", 0.0)):.3f}')}</strong></div>
            <div><span>Recall</span><strong>{_escape(f'{float(item.get("context_recall", 0.0)):.3f}')}</strong></div>
          </div>
          <div class="bar-track" style="margin-top:12px;"><div class="bar-fill" style="width:{float(item.get('context_precision', 0.0)) * 100:.0f}%"></div></div>
        </div>
        """
        for item in recent_answers[:5]
    ) or "<div class='box'><div class='small'>No evaluation history yet.</div></div>"
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>User Dashboard</title>
<style>
body{{margin:0;font-family:Segoe UI,Arial,sans-serif;background:#0e1117;color:#e6edf3}}
.wrap{{max-width:1120px;margin:0 auto;padding:32px 20px}}
.panel{{background:linear-gradient(180deg,rgba(21,26,35,.95),rgba(16,21,29,.95));border:1px solid #243041;border-radius:18px;padding:22px;margin-bottom:18px;box-shadow:0 18px 40px rgba(0,0,0,.25)}}
.grid{{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}}
.box{{background:rgba(255,255,255,.03);border:1px solid #243041;border-radius:14px;padding:14px}}
.button{{display:inline-block;padding:10px 14px;border-radius:999px;background:#1b2230;border:1px solid #243041;color:#e6edf3;text-decoration:none}}
.search-panel .input{{display:block;width:100%;min-width:0;background:rgba(255,255,255,.06);border-color:#2b3a4f;color:#e6edf3}}
.search-panel .button.primary{{width:max-content}}
.small{{color:#9aa4b2;font-size:13px}}
.metric{{font-size:12px;color:#9aa4b2;text-transform:uppercase;letter-spacing:.04em}}
.value{{font-size:28px;font-weight:700;margin-top:6px}}
.files{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}
.topline{{display:flex;justify-content:space-between;gap:14px;align-items:center;flex-wrap:wrap}}
.pill{{display:inline-flex;align-items:center;padding:6px 10px;border-radius:999px;border:1px solid #243041;background:rgba(255,255,255,.03);color:#9aa4b2;font-size:12px;margin-right:8px;margin-top:8px}}
.list{{margin:12px 0 0;padding-left:18px;color:#e6edf3}}
.list li{{margin-bottom:8px;color:#c7d0db}}
.answers{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}
.file-card{{min-width:0;overflow:hidden}}
.file-label{{font-size:12px;color:#9aa4b2;text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px}}
.file-title{{font-size:18px;font-weight:700;line-height:1.2;word-break:break-word;overflow-wrap:anywhere}}
.file-subtitle{{margin-top:8px;color:#c7d0db;font-size:13px;word-break:break-word;overflow-wrap:anywhere}}
.file-path{{display:none}}
.history-metrics{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:12px}}
.history-metrics div{{background:rgba(255,255,255,.03);border:1px solid #243041;border-radius:12px;padding:10px}}
.history-metrics span{{display:block;color:#9aa4b2;font-size:11px;text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px}}
.history-metrics strong{{font-size:16px}}
.bar-track{{height:10px;background:rgba(255,255,255,.05);border:1px solid #243041;border-radius:999px;overflow:hidden}}
.bar-fill{{height:100%;background:linear-gradient(90deg,#37d67a,#4aa3ff)}}
@media (max-width:900px){{.grid,.files{{grid-template-columns:1fr}}}}
@media (max-width:900px){{.answers{{grid-template-columns:1fr}}}}
</style></head>
<body><div class="wrap">
<div class="panel">
  <div class="topline">
    <div>
      <h1>Dashboard</h1>
      <p class="small">Signed in as {_escape(user.get("username", ""))} ({_escape(user.get("role", "user"))})</p>
    </div>
    <div>
      <a class="button" href="/">Open question page</a>
      <a class="button" href="/logout">Logout</a>
    </div>
  </div>
  <div>
    <span class="pill">Private workspace</span>
    <span class="pill">Approved corpus only</span>
    <span class="pill">No raw JSON shown here</span>
  </div>
</div>
<div class="grid">
  <div class="panel">
    <h2>Ask a question</h2>
    <p class="small">The public page handles the live question flow, answer generation, and metrics. This dashboard stays focused on your workspace, approvals, and approved data summary.</p>
    <a class="button" href="/">Open question page</a>
    <h3 style="margin:18px 0 8px;">What you can do</h3>
    <ul class="list">
      <li>Submit a question from the main page and get an answer grounded in approved files.</li>
      <li>Review the approved corpus without seeing internal retrieval traces.</li>
      <li>Return here anytime as your signed-in workspace home.</li>
    </ul>
  </div>
  <div class="panel">
    <h2>My uploads</h2>
    <form class="form-grid search-panel" method="get" action="/dashboard" style="margin-bottom:12px;">
      <input class="input" type="text" name="q" placeholder="Filter questions or uploads..." value="{_escape(search)}">
      <div><button class="button primary" type="submit">Search dashboard</button></div>
    </form>
    <div class="files">{my_upload_cards}</div>
  </div>
</div>
<div class="panel">
  <div class="topline">
    <div>
      <h2>Recent questions and answers</h2>
      <p class="small">A short history of the latest answered questions, so the dashboard feels like a live workspace instead of only a file browser.</p>
    </div>
    <a class="button" href="/">Ask a new question</a>
  </div>
  <div class="answers">{recent_answers_html}</div>
</div>
<div class="panel">
  <h2>Evaluation history</h2>
  <p class="small">This shows how the four main metrics have behaved across your recent questions, so you can quickly spot quality trends.</p>
  <div class="files">{history_cards}</div>
</div>
</div></body></html>"""


class RagDemoHandler(BaseHTTPRequestHandler):
    server_version = "RagDemoHTTP/2.0"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/logout":
            self.send_response(302)
            self.send_header("Set-Cookie", "rag_token=; Path=/; Max-Age=0; HttpOnly")
            self.send_header("Location", "/")
            self.end_headers()
            return
        if parsed.path == "/login":
            self._send_html(_render_auth_page("Login", "/login", ["identifier", "password"], "Login"))
            return
        if parsed.path == "/register":
            self._send_html(_render_auth_page("Register", "/register", ["username", "email", "password"], "Register"))
            return
        if parsed.path == "/verify-otp":
            self._send_html(_render_auth_page("Verify OTP", "/verify-otp", ["email", "otp"], "Verify"))
            return
        if parsed.path == "/admin/login":
            self._send_html(_render_auth_page("Admin Login", "/admin/login", ["identifier", "password"], "Admin login"))
            return
        if parsed.path == "/health":
            _send_json(
                self,
                {
                    "status": "ok",
                    "service": "rag-pipeline-demo",
                    "signed_in": bool(self._current_user()),
                },
            )
            return
        if parsed.path == "/":
            self._send_html(_render_result(user=self._current_user()))
            return
        if parsed.path == "/dashboard":
            user = self._current_user()
            if not user:
                self._send_html(_render_auth_page("Login", "/login", ["identifier", "password"], "Login", "Please log in to view the user dashboard."))
                return
            search = parse_qs(parsed.query).get("q", [""])[0]
            self._send_html(_render_user_dashboard(user, search=search))
            return
        if parsed.path == "/admin":
            user = self._current_user()
            if not user or user.get("role") != "admin":
                self._send_html(_render_auth_page("Admin Login", "/admin/login", ["identifier", "password"], "Admin login", "Admin credentials required."))
                return
            search = parse_qs(parsed.query).get("q", [""])[0]
            self._send_html(_render_admin(search=search))
            return
        if parsed.path == "/download":
            self._handle_download(parsed.query)
            return
        if parsed.path == "/dashboard/delete":
            self._handle_dashboard_delete(parsed.query)
            return
        if parsed.path == "/admin/action":
            self._handle_admin_action(parsed.query)
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/register":
            self._handle_register()
            return
        if parsed.path == "/verify-otp":
            self._handle_verify_otp()
            return
        if parsed.path == "/login":
            self._handle_login()
            return
        if parsed.path == "/admin/login":
            self._handle_admin_login()
            return
        if parsed.path == "/submit-upload":
            self._handle_submit_upload()
            return
        if parsed.path == "/ask":
            self._handle_ask()
            return
        self.send_error(404)

    def _handle_submit_upload(self) -> None:
        fields, files = _parse_form_fields(self)
        title = str(fields.get("upload_title", "")).strip()
        notes = str(fields.get("notes", "")).strip()
        if not title:
            self._send_html(_render_result(error="Upload title is required."))
            return
        payloads: list[tuple[str, bytes]] = []
        for _field_name, filename, data in files:
            if filename:
                payloads.append((Path(filename).name, data))
        if not payloads:
            self._send_html(_render_result(error="Please attach at least one file."))
            return
        current_user = self._current_user()
        save_pending_upload(
            payloads,
            question=title,
            notes=notes,
            uploader_key=_user_key(current_user) if current_user else "",
            uploader_username=str((current_user or {}).get("username", "")),
            uploader_email=str((current_user or {}).get("email", "")),
        )
        self._send_html(_render_admin())

    def _handle_register(self) -> None:
        fields, _files = _parse_form_fields(self)
        username = str(fields.get("username", "")).strip()
        email = str(fields.get("email", "")).strip()
        password = str(fields.get("password", "")).strip()
        if not username or not email or not password:
            self._send_html(_render_auth_page("Register", "/register", ["username", "email", "password"], "Register", "All fields are required."))
            return
        try:
            register_user(username, email, password)
            otp = generate_otp(email)
        except ValueError as exc:
            self._send_html(_render_auth_page("Register", "/register", ["username", "email", "password"], "Register", str(exc)))
            return
        self._send_html(f"<html><body><h1>OTP generated</h1><p>Your local OTP is: <strong>{_escape(otp)}</strong></p><a href='/verify-otp'>Verify OTP</a></body></html>")

    def _handle_verify_otp(self) -> None:
        fields, _files = _parse_form_fields(self)
        email = str(fields.get("email", "")).strip()
        otp = str(fields.get("otp", "")).strip()
        if not email or not otp:
            self._send_html(_render_auth_page("Verify OTP", "/verify-otp", ["email", "otp"], "Verify", "Email and OTP are required."))
            return
        if verify_otp(email, otp):
            self._send_html("<html><body><h1>Verified</h1><a href='/login'>Go to login</a></body></html>")
        else:
            self._send_html(_render_auth_page("Verify OTP", "/verify-otp", ["email", "otp"], "Verify", "Invalid or expired OTP."))

    def _handle_login(self) -> None:
        fields, _files = _parse_form_fields(self)
        identifier = str(fields.get("identifier", "")).strip()
        password = str(fields.get("password", "")).strip()
        user = authenticate_user(identifier, password)
        if not user:
            self._send_html(_render_auth_page("Login", "/login", ["identifier", "password"], "Login", "Invalid credentials or unverified email."))
            return
        token = create_token(user)
        self.send_response(302)
        self.send_header("Set-Cookie", f"rag_token={token}; Path=/; HttpOnly")
        self.send_header("Location", "/")
        self.end_headers()

    def _handle_admin_login(self) -> None:
        fields, _files = _parse_form_fields(self)
        identifier = str(fields.get("identifier", "")).strip()
        password = str(fields.get("password", "")).strip()
        reset_admin_password_from_env()
        admin_username = os.getenv("ADMIN_USERNAME", "").strip()
        admin_email = os.getenv("ADMIN_EMAIL", "").strip()
        admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
        user = authenticate_user(identifier, password)
        if not user and admin_password and password == admin_password and identifier in {admin_username, admin_email}:
            user = {
                "username": admin_username,
                "email": admin_email,
                "role": "admin",
                "verified": True,
            }
        if not user or user.get("role") != "admin":
            self._send_html(_render_auth_page("Admin Login", "/admin/login", ["identifier", "password"], "Admin login", "Admin credentials required."))
            return
        token = create_token(user)
        self.send_response(302)
        self.send_header("Set-Cookie", f"rag_token={token}; Path=/; HttpOnly")
        self.send_header("Location", "/admin")
        self.end_headers()

    def _handle_admin_action(self, query: str) -> None:
        params = parse_qs(query)
        upload_id = params.get("id", [""])[0]
        review_note = params.get("review_note", [""])[0].strip()
        decision = params.get("decision", [""])[0]
        if upload_id:
            try:
                if decision == "approve":
                    approve_upload(upload_id, review_note=review_note)
                elif decision == "reject":
                    reject_upload(upload_id, review_note=review_note)
            except FileNotFoundError:
                pass
        self._send_html(_render_admin(search=review_note))

    def _handle_download(self, query: str) -> None:
        params = parse_qs(query)
        path = params.get("path", [""])[0]
        if not path:
            self.send_error(400, "Missing path")
            return
        report_path = Path(path)
        if not report_path.exists():
            self.send_error(404, "Report not found")
            return
        data = report_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Disposition", f'attachment; filename="{report_path.name}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_ask(self) -> None:
        fields, _files = _parse_form_fields(self)
        question = str(fields.get("question", "")).strip()
        if not question:
            self._send_html(_render_result(error="Please enter a question."))
            return
        approved_dir = approved_input_dir()
        if not any(approved_dir.rglob("*")):
            self._send_html(_render_result(error="No approved files yet. Ask the admin to approve uploads first."))
            return
        try:
            result = run_cli(
                question=question,
                input_dir=approved_dir,
                chunk_size=800,
                chunk_overlap=120,
                top_k=3,
                report_dir=Path("reports") / "app_runs",
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("Local RAG demo failed")
            self._send_html(_render_result(error=f"Pipeline failed: {exc}"))
            return
        if result.get("answer", "") and result.get("report_path", ""):
            if result.get("answer_strategy") == "definition_override":
                result["why_answer"] = "This answer came from a built-in definition override because the question matched a common definition pattern."
            else:
                result["why_answer"] = result.get("why_answer") or "The answer was grounded in the approved corpus and the top retrieved chunks."
        current_user = self._current_user()
        if current_user:
            save_question_history(
                user_key=_user_key(current_user),
                username=str(current_user.get("username", "")),
                email=str(current_user.get("email", "")),
                question=question,
                answer=str(result.get("answer", "")),
                report_path=str(result.get("report_path", "")),
                context_precision=float(result.get("context_precision", 0.0)),
                answer_relevancy=float(result.get("answer_relevancy", 0.0)),
                faithfulness=float(result.get("faithfulness", 0.0)),
                context_recall=float(result.get("context_recall", 0.0)),
            )
        self._send_html(_render_result(result))

    def _handle_dashboard_delete(self, query: str) -> None:
        user = self._current_user()
        if not user:
            self._send_html(_render_auth_page("Login", "/login", ["identifier", "password"], "Login", "Please log in to manage your dashboard history."))
            return
        params = parse_qs(query)
        report_path = params.get("report_path", [""])[0]
        if report_path:
            delete_question_history(user_key=_user_key(user), report_path=report_path)
        search = params.get("q", [""])[0]
        self._send_html(_render_user_dashboard(user, search=search))

    def _current_user(self) -> dict[str, object] | None:
        token = _cookie_value(self.headers.get("Cookie"), "rag_token")
        return verify_token(token) if token else None

    def _send_html(self, html_text: str) -> None:
        data = html_text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        logger.info("%s - %s", self.address_string(), format % args)


def serve_demo(host: str = "127.0.0.1", port: int = 8000) -> None:
    load_dotenv()
    bootstrap_admin_from_env()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    server = ThreadingHTTPServer((host, port), RagDemoHandler)
    logger.info("RAG demo available at http://%s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down demo server")
    finally:
        server.server_close()
