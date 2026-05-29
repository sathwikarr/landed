"""Email notification service using Resend (free: 3000 emails/mo)."""
import os
import resend
from datetime import datetime

resend.api_key = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@jobapply.app")


def send_daily_digest(to_email: str, stats: dict, applications: list):
    subject = f"JobApply — {stats.get('apps_submitted', 0)} applications submitted today"
    app_rows = "".join([
        f"<tr><td>{a['company']}</td><td>{a['role']}</td><td>{a['status']}</td></tr>"
        for a in applications[:20]
    ])
    html = f"""
    <h2>Your JobApply Daily Digest</h2>
    <p>{datetime.now().strftime('%B %d, %Y')}</p>
    <table border="1" cellpadding="6" style="border-collapse:collapse">
      <tr><th>Stat</th><th>Count</th></tr>
      <tr><td>Jobs found</td><td>{stats.get('jobs_found', 0)}</td></tr>
      <tr><td>After dedup</td><td>{stats.get('jobs_after_dedup', 0)}</td></tr>
      <tr><td>Applied</td><td>{stats.get('apps_submitted', 0)}</td></tr>
      <tr><td>Flagged (need review)</td><td>{stats.get('apps_flagged', 0)}</td></tr>
    </table>
    <h3>Applications</h3>
    <table border="1" cellpadding="6" style="border-collapse:collapse">
      <tr><th>Company</th><th>Role</th><th>Status</th></tr>
      {app_rows}
    </table>
    <p><a href="{os.environ.get('APP_URL', 'http://localhost:3000')}/tracker">View full tracker →</a></p>
    """
    resend.Emails.send({"from": FROM_EMAIL, "to": to_email, "subject": subject, "html": html})


def send_captcha_alert(to_email: str, company: str, job_title: str, job_url: str):
    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": f"⚠️ Manual action needed — {company}",
        "html": f"""
        <h3>CAPTCHA detected — manual action needed</h3>
        <p><b>{job_title}</b> at <b>{company}</b></p>
        <p><a href="{job_url}">Open job posting</a></p>
        <p><a href="{os.environ.get('APP_URL', 'http://localhost:3000')}/queue">Go to review queue →</a></p>
        """
    })


def send_run_complete(to_email: str, stats: dict):
    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": f"✅ JobApply run complete — {stats.get('apps_submitted', 0)} applied",
        "html": f"""
        <h3>Run complete!</h3>
        <p>Applied: <b>{stats.get('apps_submitted', 0)}</b> &nbsp;|&nbsp; Flagged: <b>{stats.get('apps_flagged', 0)}</b></p>
        <p><a href="{os.environ.get('APP_URL', 'http://localhost:3000')}/dashboard">View dashboard →</a></p>
        """
    })
