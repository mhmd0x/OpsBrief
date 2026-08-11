const refreshButton =
    document.querySelector("#refresh-button");
const statusMessage =
    document.querySelector("#status-message");
const searchInput =
    document.querySelector("#work-order-search");
const priorityFilter =
    document.querySelector("#priority-filter");
const workOrderDialog =
    document.querySelector("#work-order-dialog");
const closeDialogButton =
    document.querySelector("#close-dialog");
const recurringIssueDialog =
    document.querySelector("#recurring-issue-dialog");
const closeRecurringDialogButton =
    document.querySelector("#close-recurring-dialog");

let currentHighAttentionWorkOrders = [];
let currentAssetNames = new Map();
let currentTimezone = "UTC";

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

function openWorkOrderDetails(
    workOrder,
    timezone,
    assetNames,
) {
    const assetName =
        assetNames.get(workOrder.asset_id) ?? "Unknown asset";

    document.querySelector("#detail-title").textContent =
        workOrder.title;
    document.querySelector("#detail-asset").textContent =
        assetName;
    document.querySelector("#detail-priority").textContent =
        workOrder.priority;
    document.querySelector("#detail-status").textContent =
        workOrder.status.replaceAll("_", " ");
    document.querySelector("#detail-due-date").textContent =
        formatDate(workOrder.due_date, timezone);
    document.querySelector("#detail-failure-code").textContent =
        workOrder.failure_code ?? "Not assigned";
    document.querySelector("#detail-description").textContent =
        workOrder.description ?? "No description provided.";

    workOrderDialog.showModal();
}

function renderHighAttention(workOrders, timezone, assetNames) {
    const tableBody =
        document.querySelector("#high-attention-body");
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
        const titleButton = document.createElement("button");

        titleButton.type = "button";
        titleButton.className = "work-order-link";
        titleButton.textContent = workOrder.title;
        titleButton.addEventListener("click", () => {
            openWorkOrderDetails(
                workOrder,
                timezone,
                assetNames,
            );
        });

        titleCell.append(titleButton);

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

        const titleButton = document.createElement("button");

        titleButton.type = "button";
        titleButton.className = "work-order-link";
        titleButton.textContent = workOrder.title;
        titleButton.addEventListener("click", () => {
            openWorkOrderDetails(
                workOrder,
                timezone,
                assetNames,
            );
        });

        title.append(titleButton);
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
        const assetName = assetNames.get(workOrder.asset_id) ?? "Unknown asset";

        const titleButton = document.createElement("button");

        titleButton.type = "button";
        titleButton.className = "work-order-link";
        titleButton.textContent = workOrder.title;
        titleButton.addEventListener("click", () => {
            openWorkOrderDetails(
                workOrder,
                timezone,
                assetNames,
            );
        });

        title.append(titleButton);
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

function openRecurringIssueDetails(issue, timezone) {
    document.querySelector(
        "#recurring-detail-asset",
    ).textContent = issue.asset_name;
    document.querySelector(
        "#recurring-detail-code",
    ).textContent = issue.failure_code;
    document.querySelector(
        "#recurring-detail-count",
    ).textContent = String(issue.occurrence_count);
    document.querySelector(
        "#recurring-detail-latest",
    ).textContent = formatDate(
        issue.latest_occurrence,
        timezone,
    );
    document.querySelector(
        "#recurring-detail-action",
    ).textContent =
        `This failure has occurred ${issue.occurrence_count} times. ` +
        "Review the maintenance history and begin root-cause analysis.";

    recurringIssueDialog.showModal();
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

        const titleButton = document.createElement("button");

        titleButton.type = "button";
        titleButton.className = "work-order-link";
        titleButton.textContent = issue.asset_name;
        titleButton.addEventListener("click", () => {
            openRecurringIssueDetails(issue, timezone);
        });

title.append(titleButton);
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

function applyHighAttentionFilters() {
    const searchTerm = searchInput.value.trim().toLowerCase();
    const selectedPriority = priorityFilter.value;

    const filteredWorkOrders =
        currentHighAttentionWorkOrders.filter((workOrder) => {
            const assetName =
                currentAssetNames.get(workOrder.asset_id) ?? "";
            const searchableText = [
                assetName,
                workOrder.title,
                workOrder.failure_code ?? "",
            ]
                .join(" ")
                .toLowerCase();

            const matchesSearch =
                searchableText.includes(searchTerm);
            const matchesPriority =
                selectedPriority === ""
                || workOrder.priority === selectedPriority;

            return matchesSearch && matchesPriority;
        });

    renderHighAttention(
        filteredWorkOrders,
        currentTimezone,
        currentAssetNames,
    );
}

function renderMonthlyPMCompliance(compliance) {
    const [
        year,
        month,
    ] = compliance.month.split("-").map(Number);

    const monthLabel = new Intl.DateTimeFormat(
        "en",
        {
            month: "long",
            year: "numeric",
            timeZone: "UTC",
        },
    ).format(new Date(Date.UTC(year, month - 1, 1)));

    document.querySelector("#pm-month").textContent =
        `${monthLabel} preventive-maintenance plan`;
    document.querySelector("#pm-planned-count").textContent =
        compliance.planned_count;
    document.querySelector("#pm-completed-count").textContent =
        compliance.completed_count;
    document.querySelector("#pm-remaining-count").textContent =
        compliance.remaining_count;
    document.querySelector("#pm-overdue-count").textContent =
        compliance.overdue_count;
    document.querySelector(
        "#pm-completion-percentage",
    ).textContent = `${compliance.completion_percentage}%`;

    const progressTrack =
        document.querySelector(".pm-progress-track");
    const progressBar =
        document.querySelector("#pm-progress-bar");
    const percentage = Math.min(
        Math.max(compliance.completion_percentage, 0),
        100,
    );

    progressBar.style.width = `${percentage}%`;
    progressTrack.setAttribute(
        "aria-valuenow",
        String(percentage),
    );

    const planStatus =
        document.querySelector("#pm-plan-status");

    planStatus.className = "pm-plan-status";

    if (compliance.planned_count === 0) {
        planStatus.textContent = "No PM plan";
    } else if (compliance.on_plan) {
        planStatus.textContent = "On plan";
        planStatus.classList.add(
            "pm-plan-status--success",
        );
    } else {
        planStatus.textContent = "Behind plan";
        planStatus.classList.add(
            "pm-plan-status--danger",
        );
    }

    const requiredPace =
        document.querySelector("#pm-required-pace");

    if (compliance.remaining_count === 0) {
        requiredPace.textContent =
            "The monthly preventive-maintenance plan is complete.";
    } else {
        requiredPace.textContent =
            `${compliance.completed_to_date_count} of ` +
            `${compliance.planned_to_date_count} PMs due through ` +
            `today are complete. ${compliance.required_per_day} ` +
            `PMs per calendar day are required across the remaining ` +
            `${compliance.calendar_days_remaining} days to reach 100%.`;
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

    currentHighAttentionWorkOrders =
        brief.high_attention_work_orders;
    currentAssetNames = assetNames;
    currentTimezone = timezone;

    applyHighAttentionFilters();
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
        const [
            briefResponse,
            assetsResponse,
            pmResponse,
        ] = await Promise.all([
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
            fetch("/insights/monthly-pm-compliance", {
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

        if (!pmResponse.ok) {
            throw new Error(
                `The PM API returned status ${pmResponse.status}.`,
            );
        }

        const [
            brief,
            assets,
            pmCompliance,
        ] = await Promise.all([
            briefResponse.json(),
            assetsResponse.json(),
            pmResponse.json(),
        ]);

        const assetNames = new Map(
            assets.map((asset) => [asset.id, asset.name]),
        );

        renderBrief(brief, assetNames);
        renderMonthlyPMCompliance(pmCompliance);

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
closeRecurringDialogButton.addEventListener("click", () => {
    recurringIssueDialog.close();
});
closeDialogButton.addEventListener("click", () => {
    workOrderDialog.close();
});
searchInput.addEventListener(
    "input",
    applyHighAttentionFilters,
);
priorityFilter.addEventListener(
    "change",
    applyHighAttentionFilters,
);
refreshButton.addEventListener("click", loadBrief);
loadBrief();