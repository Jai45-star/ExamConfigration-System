"""
admin/reports.py — Reporting logic for exporting data.
"""
import csv
import io
from typing import List, Dict

def generate_csv_report(data: List[Dict]) -> str:
    """Converts a list of dicts to a CSV string."""
    if not data:
        return ""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()
