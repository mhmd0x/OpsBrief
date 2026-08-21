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
const pmListDialog =
    document.querySelector("#pm-list-dialog");
const closePMListDialogButton =
    document.querySelector("#close-pm-list-dialog");
const pmMetricButtons =
    document.querySelectorAll("[data-pm-list]");

let currentHighAttentionWorkOrders = [];
let currentAssetNames = new Map();
let currentTimezone = "UTC";
let currentPMCompliance = null;

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

function openPMWorkOrderList(category) {
    if (!currentPMCompliance) {
        return;
    }

    const categories = {
        planned: {
            title: "Planned PM work orders",
            field: "planned_work_orders",
        },
        completed: {
            title: "Completed PM work orders",
            field: "completed_work_orders",
        },
        remaining: {
            title: "Remaining PM work orders",
            field: "remaining_work_orders",
        },
        overdue: {
            title: "Overdue PM work orders",
            field: "overdue_work_orders",
        },
    };

    const selectedCategory = categories[category];

    if (!selectedCategory) {
        return;
    }

    const workOrders =
        currentPMCompliance[selectedCategory.field];
    const container =
        document.querySelector("#pm-list-content");

    document.querySelector("#pm-list-title").textContent =
        selectedCategory.title;
    container.replaceChildren();

    if (workOrders.length === 0) {
        container.append(
            createEmptyState(
                `No ${category} PM work orders.`,
            ),
        );
        pmListDialog.showModal();
        return;
    }

    for (const workOrder of workOrders) {
        const item = document.createElement("article");
        item.className = "item";

        const details = document.createElement("div");
        const title = document.createElement("h3");
        const titleButton =
            document.createElement("button");
        const description = document.createElement("p");
        const dueDate = document.createElement("span");

        const assetName =
            currentAssetNames.get(workOrder.asset_id)
            ?? "Unknown asset";

        titleButton.type = "button";
        titleButton.className = "work-order-link";
        titleButton.textContent = workOrder.title;
        titleButton.addEventListener("click", () => {
            pmListDialog.close();
            openWorkOrderDetails(
                workOrder,
                currentTimezone,
                currentAssetNames,
            );
        });

        title.append(titleButton);
        description.textContent =
            `${assetName} · ` +
            `${workOrder.status.replaceAll("_", " ")}`;
        dueDate.className = "item-value";

        if (workOrder.status === "completed") {
            dueDate.classList.add(
                "item-value--success",
            );
        } else if (
            new Date(workOrder.due_date) < new Date()
        ) {
            dueDate.classList.add(
                "item-value--danger",
            );
        }

        dueDate.textContent = formatDate(
            workOrder.due_date,
            currentTimezone,
        );

        details.append(title, description);
        item.append(details, dueDate);
        container.append(item);
    }

    pmListDialog.showModal();
}

function renderMonthlyPMCompliance(compliance) {
    currentPMCompliance = compliance;
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

function renderYearToDatePMCompliance(compliance) {
    document.querySelector("#ytd-pm-summary").textContent =
        `${compliance.completed_count} of ` +
        `${compliance.planned_count} planned PMs completed ` +
        `in ${compliance.year}`;

    document.querySelector(
        "#ytd-pm-percentage",
    ).textContent = `${compliance.completion_percentage}%`;

    const container =
        document.querySelector("#ytd-pm-chart");
    container.replaceChildren();

    if (compliance.months.length === 0) {
        container.append(
            createEmptyState(
                "No year-to-date PM data is available.",
            ),
        );
        return;
    }

    const maximumPlanned = Math.max(
        ...compliance.months.map(
            (month) => month.planned_count,
        ),
        1,
    );

    for (const month of compliance.months) {
        const monthColumn = document.createElement("div");
        monthColumn.className = "ytd-month";

        const bars = document.createElement("div");
        bars.className = "ytd-bars";

        const plannedBar = document.createElement("div");
        plannedBar.className =
            "ytd-bar ytd-bar--planned";
        plannedBar.style.height =
            `${month.planned_count / maximumPlanned * 100}%`;
        plannedBar.title =
            `${month.planned_count} planned PMs`;

        const completedBar = document.createElement("div");
        completedBar.className =
            "ytd-bar ytd-bar--completed";
        completedBar.style.height =
            `${month.completed_count / maximumPlanned * 100}%`;
        completedBar.title =
            `${month.completed_count} completed PMs`;

        const monthLabel = document.createElement("span");
        monthLabel.className = "ytd-month-label";
        monthLabel.textContent = new Intl.DateTimeFormat(
            "en",
            {
                month: "short",
                timeZone: "UTC",
            },
        ).format(
            new Date(`${month.month}-01T00:00:00Z`),
        );

        const monthValue = document.createElement("span");
        monthValue.className = "ytd-month-value";
        monthValue.textContent =
            `${month.completed_count}/` +
            `${month.planned_count} · ` +
            `${month.completion_percentage}%`;

        bars.append(plannedBar, completedBar);
        monthColumn.append(
            bars,
            monthLabel,
            monthValue,
        );
        container.append(monthColumn);
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

function renderAssetReliabilityRanking(rankings) {
    const tableBody = document.querySelector(
        "#asset-reliability-body",
    );
    tableBody.replaceChildren();

    if (rankings.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 8;
        cell.textContent = "No assets are available.";
        row.append(cell);
        tableBody.append(row);
        return;
    }

    for (const [index, asset] of rankings.entries()) {
        const row = document.createElement("tr");

        const rankCell = document.createElement("td");
        rankCell.className = "reliability-rank";
        rankCell.textContent = `#${index + 1}`;

        const assetCell = document.createElement("td");
        assetCell.textContent = asset.asset_name;

        const tagCell = document.createElement("td");
        tagCell.textContent = asset.asset_tag;

        const activeCell = document.createElement("td");
        activeCell.textContent =
            asset.active_work_order_count;

        const overdueCell = document.createElement("td");
        overdueCell.textContent =
            asset.overdue_work_order_count;

        const highPriorityCell =
            document.createElement("td");
        highPriorityCell.textContent =
            asset.high_priority_work_order_count;

        const recurringCell = document.createElement("td");
        recurringCell.textContent =
            asset.recurring_issue_count;

        const scoreCell = document.createElement("td");
        const score = document.createElement("span");
        score.className = "risk-score";
        score.textContent = asset.risk_score;

        if (asset.risk_score >= 12) {
            score.classList.add("risk-score--high");
        } else if (asset.risk_score >= 5) {
            score.classList.add("risk-score--medium");
        }

        scoreCell.append(score);
        row.append(
            rankCell,
            assetCell,
            tagCell,
            activeCell,
            overdueCell,
            highPriorityCell,
            recurringCell,
            scoreCell,
        );
        tableBody.append(row);
    }
}

function renderBacklogAging(backlog) {
    document.querySelector(
        "#backlog-total-count",
    ).textContent = backlog.total_backlog_count;

    document.querySelector(
        "#backlog-aging-summary",
    ).textContent =
        `${backlog.total_backlog_count} active work orders ` +
        `grouped by age`;

    document.querySelector(
        "#backlog-average-age",
    ).textContent = `${backlog.average_age_days} days`;

    document.querySelector(
        "#backlog-oldest-age",
    ).textContent = `${backlog.oldest_age_days} days`;

    const container = document.querySelector(
        "#backlog-aging-buckets",
    );
    container.replaceChildren();

    for (const [index, bucket] of backlog.buckets.entries()) {
        const bucketElement =
            document.createElement("article");
        bucketElement.className =
            "backlog-aging-bucket";

        if (index === 2) {
            bucketElement.classList.add(
                "backlog-aging-bucket--warning",
            );
        }

        if (index === 3) {
            bucketElement.classList.add(
                "backlog-aging-bucket--danger",
            );
        }

        const label = document.createElement("span");
        label.textContent = bucket.label;

        const count = document.createElement("strong");
        count.textContent = bucket.work_order_count;

        bucketElement.append(label, count);
        container.append(bucketElement);
    }
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
            ytdPMResponse,
            backlogResponse,
            reliabilityResponse,
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
            fetch("/insights/ytd-pm-compliance", {
                headers: {
                    Accept: "application/json",
                },
            }),
            fetch("/insights/work-order-backlog-aging", {
                headers: {
                    Accept: "application/json",
                },
            }),
            fetch("/insights/asset-reliability-ranking", {
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

        if (!ytdPMResponse.ok) {
            throw new Error(
                `The YTD PM API returned status ` +
                `${ytdPMResponse.status}.`,
            );
        }

        if (!backlogResponse.ok) {
            throw new Error(
                `The backlog-aging API returned status ` +
                `${backlogResponse.status}.`,
            );
        }
        if (!reliabilityResponse.ok) {
            throw new Error(
                `The asset-reliability API returned status ` +
                `${reliabilityResponse.status}.`,
            );
        }

        const [
            brief,
            assets,
            pmCompliance,
            ytdPMCompliance,
            backlogAging,
            reliabilityRankings,
        ] = await Promise.all([
            briefResponse.json(),
            assetsResponse.json(),
            pmResponse.json(),
            ytdPMResponse.json(),
            backlogResponse.json(),
            reliabilityResponse.json(),
        ]);

        const assetNames = new Map(
            assets.map((asset) => [asset.id, asset.name]),
        );

        renderBrief(brief, assetNames);
        renderMonthlyPMCompliance(pmCompliance);
        renderYearToDatePMCompliance(
            ytdPMCompliance,
        );
        renderBacklogAging(backlogAging);
        renderAssetReliabilityRanking(
            reliabilityRankings,
        );

        statusMessage.className =
            "status-message status-message--success";
        statusMessage.textContent =
            "Operational data is current";
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

for (const button of pmMetricButtons) {
    button.addEventListener("click", () => {
        openPMWorkOrderList(button.dataset.pmList);
    });
}

closeRecurringDialogButton.addEventListener("click", () => {
    recurringIssueDialog.close();
});
closePMListDialogButton.addEventListener("click", () => {
    pmListDialog.close();
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