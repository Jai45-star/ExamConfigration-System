"""
admin/dashboard.py — Dashboard helper functions.
"""
def format_dashboard_summary(total, verified, rejected, revoked):
    """Simple formatter for dashboard text if needed."""
    return f"Status: {total} registered, {verified} verified, {rejected} rejected, {revoked} revoked."
