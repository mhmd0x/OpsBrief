const refreshButton = document.querySelector("#refresh-button");
const statusMessage = document.querySelector("#status-message");

function formatDate(value, timezone) {
    if (!value) {
        return "Not set";
    }

    return new Intl.DateTimeFormat("en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: timezone,
    }).format(new Date(value));
}

function createBadge(value, extraClass = "") {
    const badge = document.createElement("span");
    badge.className = `badge ${extraClass}`.trim();
    badge.textContent = value.replaceAll("_", " ");
    return badge;
}

function createEmptyState(message) {
    const paragraph = document.createElement("p");
    paragraph.className = "empty-state";
    paragraph.textContent = message;
    return paragraph;
}

function renderHighAttention(workOrders, timezone, assetNames) {
    const tableBody = document.querySelector("#high-attention-body");
    tableBody.replaceChildren();

    if (workOrders.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 6;
        cell.textContent = "No high-attention work orders.";
        row.append(cell);
        tableBody.append(row);
        return;
    }

    for (const workOrder of workOrders) {
        const row = document.createElement("tr");

        const assetCell = document.createElement("td");
        assetCell.textContent =
            assetNames.get(workOrder.asset_id) ?? "Unknown asset";


        const titleCell = document.createElement("td");
        titleCell.textContent = workOrder.title;

        const priorityCell = document.createElement("td");
        priorityCell.append(
            createBadge(
                workOrder.priority,
                workOrder.priority === "high" ? "badge--high" : "",
            ),
        );

        const statusCell = document.createElement("td");
        statusCell.append(createBadge(workOrder.status));

        const dueDateCell = document.createElement("td");
        dueDateCell.textContent = formatDate(
            workOrder.due_date,
            timezone,
        );

        const failureCodeCell = document.createElement("td");
        failureCodeCell.textContent =
            workOrder.failure_code ?? "Not assigned";

        row.append(
            assetCell,
            titleCell,
            priorityCell,
            statusCell,
            dueDateCell,
            failureCodeCell,
        );
        tableBody.append(row);
    }
}

function renderOverdue(workOrders, timezone, assetNames) {
    const container = document.querySelector("#overdue-list");
    container.replaceChildren();

    if (workOrders.length === 0) {
        container.append(
            createEmptyState("No overdue work orders."),
        );
        return;
    }

    for (const workOrder of workOrders) {
        const item = document.createElement("article");
        item.className = "item";

        const details = document.createElement("div");
        const title = document.createElement("h3");
        const description = document.createElement("p");
        const dueDate = document.createElement("span");
        const assetName =
            assetNames.get(workOrder.asset_id) ?? "Unknown asset";

        title.textContent = workOrder.title;
        description.textContent =
            `${assetName} · ` +
            `${workOrder.status.replaceAll("_", " ")} · ` +
            `${workOrder.failure_code ?? "No failure code"}`;
        dueDate.className = "item-value";
        dueDate.textContent = formatDate(
            workOrder.due_date,
            timezone,
        );

        details.append(title, description);
        item.append(details, dueDate);
        container.append(item);
    }
}

function renderDueSoon(workOrders, timezone, assetNames) {
    const container = document.querySelector("#due-soon-list");
    container.replaceChildren();

    if (workOrders.length === 0) {
        container.append(
            createEmptyState(
                "No work orders are due within seven days.",
            ),
        );
        return;
    }

    for (const workOrder of workOrders) {
        const item = document.createElement("article");
        item.className = "item";

        const details = document.createElement("div");
        const title = document.createElement("h3");
        const description = document.createElement("p");
        const dueDate = document.createElement("span");
        const assetName =
            assetNames.get(workOrder.asset_id) ?? "Unknown asset";

        title.textContent = workOrder.title;
        description.textContent =
            `${assetName} · ` +
            `${workOrder.status.replaceAll("_", " ")} · ` +
            `${workOrder.priority} priority`;
        dueDate.className = "item-value";
        dueDate.textContent = formatDate(
            workOrder.due_date,
            timezone,
        );

        details.append(title, description);
        item.append(details, dueDate);
        container.append(item);
    }
}

function renderRecurring(issues, timezone) {
    const container = document.querySelector("#recurring-list");
    container.replaceChildren();

    if (issues.length === 0) {
        container.append(
            createEmptyState("No recurring issues detected."),
        );
        return;
    }

    for (const issue of issues) {
        const item = document.createElement("article");
        item.className = "item";

        const details = document.createElement("div");
        const title = document.createElement("h3");
        const description = document.createElement("p");
        const count = document.createElement("span");

        title.textContent = issue.asset_name;
        description.textContent =
            `${issue.failure_code} · Latest: ` +
            formatDate(issue.latest_occurrence, timezone);
        count.className = "item-value";
        count.textContent = `${issue.occurrence_count} occurrences`;

        details.append(title, description);
        item.append(details, count);
        container.append(item);
    }
}

function renderBrief(brief, assetNames) {
    const { summary, timezone } = brief;

    document.querySelector("#overdue-count").textContent =
        summary.overdue_count;
    document.querySelector("#due-today-count").textContent =
        summary.due_today_count;
    document.querySelector("#due-soon-count").textContent =
        summary.due_soon_count;
    document.querySelector("#high-attention-count").textContent =
        summary.high_attention_count;
    document.querySelector("#recurring-issue-count").textContent =
        summary.recurring_issue_count;
    document.querySelector("#timezone").textContent = timezone;
    document.querySelector("#generated-at").textContent =
        `Generated ${formatDate(brief.generated_at, timezone)}`;

    renderHighAttention(
        brief.high_attention_work_orders,
        timezone,
        assetNames,
    );
    renderOverdue(
        brief.overdue_work_orders,
        timezone,
        assetNames,
    );
    renderDueSoon(
        brief.due_soon_work_orders,
        timezone,
        assetNames,
    );
    renderRecurring(brief.recurring_issues, timezone);
}

async function loadBrief() {
    refreshButton.disabled = true;
    statusMessage.className = "status-message";
    statusMessage.textContent = "Refreshing operational data…";

    try {
        const [briefResponse, assetsResponse] = await Promise.all([
    fetch("/briefs/daily", {
        headers: {
            Accept: "application/json",
        },
    }),
    fetch("/assets", {
        headers: {
            Accept: "application/json",
        },
    }),
]);

if (!briefResponse.ok) {
    throw new Error(
        `The brief API returned status ${briefResponse.status}.`,
    );
}

if (!assetsResponse.ok) {
    throw new Error(
        `The assets API returned status ${assetsResponse.status}.`,
    );
}

const [brief, assets] = await Promise.all([
    briefResponse.json(),
    assetsResponse.json(),
]);

const assetNames = new Map(
    assets.map((asset) => [asset.id, asset.name]),
);

renderBrief(brief, assetNames);

        statusMessage.className =
            "status-message status-message--success";
        statusMessage.textContent = "Operational data is current";
    } catch (error) {
        console.error(error);
        statusMessage.className =
            "status-message status-message--error";
        statusMessage.textContent =
            "The Daily Operations Brief could not be loaded.";
    } finally {
        refreshButton.disabled = false;
    }
}

refreshButton.addEventListener("click", loadBrief);
loadBrief();