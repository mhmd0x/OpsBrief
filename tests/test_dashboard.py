from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "OpsBrief" in response.text
    assert "Daily Operations Brief" in response.text
    assert "Due soon" in response.text
    assert "due-soon-count" in response.text
    assert "due-soon-list" in response.text
    assert "<th>Asset</th>" in response.text
    assert "work-order-search" in response.text
    assert "priority-filter" in response.text
    assert "work-order-dialog" in response.text
    assert "detail-asset" in response.text
    assert "recurring-issue-dialog" in response.text
    assert "close-recurring-dialog" in response.text
    assert "Monthly PM compliance" in response.text
    assert "pm-planned-count" in response.text
    assert "pm-completion-percentage" in response.text
    assert "pm-progress-bar" in response.text
    assert "pm-required-pace" in response.text
    assert 'data-pm-list="planned"' in response.text
    assert 'data-pm-list="completed"' in response.text
    assert "pm-list-dialog" in response.text
    assert "pm-list-content" in response.text
    assert "Year-to-date PM compliance" in response.text
    assert "ytd-pm-percentage" in response.text
    assert "ytd-pm-chart" in response.text


def test_dashboard_stylesheet() -> None:
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


def test_dashboard_javascript() -> None:
    response = client.get("/static/dashboard.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert 'fetch("/assets"' in response.text
    assert "assetNames" in response.text
    assert "applyHighAttentionFilters" in response.text
    assert "openWorkOrderDetails" in response.text
    assert "showModal" in response.text
    assert "openRecurringIssueDetails" in response.text
    assert "recurringIssueDialog.showModal" in response.text
    assert "recurringIssueDialog.close" in response.text
    assert "renderMonthlyPMCompliance" in response.text
    assert (
        'fetch("/insights/monthly-pm-compliance"'
        in response.text
    )
    assert "openPMWorkOrderList" in response.text
    assert "pmMetricButtons" in response.text
    assert "renderYearToDatePMCompliance" in response.text
    assert (
        'fetch("/insights/ytd-pm-compliance"'
        in response.text
    )