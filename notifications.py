import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_TOPICS_FILE = Path(__file__).parent / ".topics"


def _load_topics():
    """Load topic mappings from .topics file."""
    topics = {}
    if not _TOPICS_FILE.exists():
        return topics
    for line in _TOPICS_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            # Strip inline comments (# ...)
            if "#" in value:
                value = value[:value.index("#")]
            topics[key.strip()] = value.strip().strip('"').strip("'")
    return topics


def _get_ntfy_config(topic_key=None):
    """Load NTFY configuration from environment and .topics file."""
    server = os.getenv("NTFY_SERVER_URL", "").strip().rstrip("/")
    username = os.getenv("NTFY_USERNAME", "")
    password = os.getenv("NTFY_PASSWORD", "")

    # Ensure server URL has a scheme
    if server and not server.startswith(("http://", "https://")):
        server = f"https://{server}"

    # Resolve topic: explicit env var > .topics file lookup > first .topics value
    topic = os.getenv("NTFY_TOPIC", "").strip()
    if not topic:
        topics = _load_topics()
        if topic_key and topic_key in topics:
            topic = topics[topic_key]
        elif topics:
            # Default to first topic found
            topic = next(iter(topics.values()))

    if not server or not topic:
        raise ValueError(
            "Missing NTFY config. Set NTFY_SERVER_URL and NTFY_TOPIC in .env, "
            "or define topics in .topics file."
        )

    return {
        "url": f"{server}/{topic}",
        "username": username,
        "password": password,
    }


def send_notification(title, message, priority=3, tags=None, topic_key=None):
    """Send a notification via NTFY."""
    config = _get_ntfy_config(topic_key=topic_key)

    cmd = [
        "curl", "-s",
        "-u", f"{config['username']}:{config['password']}",
        "-H", f"Title: {title}",
        "-H", f"Priority: {priority}",
    ]

    if tags:
        cmd.extend(["-H", f"Tags: {tags}"])

    cmd.extend(["-d", message, config["url"]])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return {"ok": result.returncode == 0, "response": result.stdout}


def notify_risk_breach(check_name, details):
    """Send a high-priority risk breach alert."""
    title = f"Risk Breach: {check_name}"
    message = details if isinstance(details, str) else str(details)
    return send_notification(title, message, priority=5, tags="warning,skull", topic_key="NTFY_TOPIC_CRITICAL")


def notify_order_fill(order):
    """Send notification for an order fill."""
    title = f"Order Filled: {order.get('symbol', 'Unknown')}"
    message = (
        f"Symbol: {order.get('symbol')}\n"
        f"Side: {order.get('side')}\n"
        f"Qty: {order.get('qty')}\n"
        f"Price: {order.get('price', 'market')}"
    )
    return send_notification(title, message, priority=3, tags="white_check_mark", topic_key="NTFY_TOPIC_MOVES")


def notify_daily_summary(summary):
    """Send a daily risk summary report."""
    lines = ["Daily Risk Report", ""]

    # Daily P&L
    dpnl = summary.get("daily_pnl", {})
    lines.append(f"Daily P&L: {dpnl.get('daily_pnl_pct', 0):+.2f}% (${dpnl.get('daily_pnl', 0):+,.2f})")

    # Drawdown
    dd = summary.get("drawdown", {})
    lines.append(f"Drawdown: {dd.get('current_drawdown_pct', 0):.2f}% (limit: {dd.get('limit_pct', 'N/A')}%)")

    # Concentration
    conc = summary.get("concentration", {})
    violations = conc.get("violations", [])
    if violations:
        lines.append(f"Concentration violations: {len(violations)}")
        for v in violations:
            lines.append(f"  {v['symbol']}: {v['pct_of_portfolio']:.1f}%")
    else:
        lines.append("Concentration: OK")

    # Overall
    lines.append("")
    lines.append("BREACHES DETECTED" if summary.get("has_breaches") else "ALL CLEAR")

    message = "\n".join(lines)
    priority = 4 if summary.get("has_breaches") else 3
    tags = "chart_with_downwards_trend" if summary.get("has_breaches") else "chart_with_upwards_trend"

    return send_notification("Daily Risk Summary", message, priority=priority, tags=tags, topic_key="NTFY_TOPIC_RECOMMENDATIONS")


if __name__ == "__main__":
    print("=== NTFY Notifications ===\n")

    try:
        config = _get_ntfy_config()
        print(f"Server: {config['url']}")
        print(f"Auth: {'configured' if config['username'] else 'none'}")

        print("\nSending test notification...")
        result = send_notification("Test", "Risk management notification test", priority=2, tags="test_tube")
        print(f"Result: {'OK' if result['ok'] else 'FAILED'}")
        if result["response"]:
            print(f"Response: {result['response'][:200]}")
    except ValueError as e:
        print(f"Config error: {e}")
