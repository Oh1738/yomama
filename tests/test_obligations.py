# tests/test_obligations.py
from datetime import date
from patur.obligations import obligations_for_year

def test_declaration_and_return_dates():
    obs = {o.name: o.due for o in obligations_for_year(2026)}
    assert obs["הצהרת מחזור שנתית"] == date(2027, 1, 31)
    assert obs["דוח שנתי (1301)"] == date(2027, 4, 30)
