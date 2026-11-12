from datetime import date
from html import escape

from entries import Entry


def render_month(year: int, month: int, entries: list[tuple[date, Entry]]) -> str:
    title = f"Дневник за {month:02d}.{year:04d}"
    rows = []
    for day, entry in entries:
        cells = (f"{day:%d.%m.%Y}", entry.feelings, entry.methods, entry.notes)
        rows.append("<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in cells) + "</tr>")
    if not rows:
        rows.append('<tr><td colspan="4">За этот месяц записей нет.</td></tr>')
    body = "\n".join(rows)
    return f"""<!doctype html>
<html lang="ru">
<meta charset="utf-8">
<title>{title}</title>
<style>
    body {{ font: 11pt system-ui, sans-serif; }}
    table {{ width: 100%; table-layout: fixed; border-collapse: collapse; }}
    th, td {{ border: 1px solid #777; padding: 6px; text-align: left; vertical-align: top; }}
    th:first-child {{ width: 7em; }}
    td {{ white-space: pre-wrap; overflow-wrap: anywhere; }}
    @media print {{ thead {{ display: table-header-group; }} }}
</style>
<h1>{title}</h1>
<table>
    <thead><tr><th>Дата</th><th>Ощущения</th><th>Методы</th><th>Заметки</th></tr></thead>
    <tbody>
{body}
    </tbody>
</table>
</html>
"""
