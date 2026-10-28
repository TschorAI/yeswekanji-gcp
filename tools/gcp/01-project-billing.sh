#!/usr/bin/env bash
# Create the project, link billing, create the budget alert.
# Reads: config.env (PROJECT_ID, PROJECT_NAME, BILLING_ACCOUNT, BUDGET_*). Writes: GCP resources.
# Idempotent: each step checks before it creates. Costs nothing by itself.
source "$(dirname "$0")/lib.sh"

step "project $PROJECT_ID"
if gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then ok "exists"
else gcloud projects create "$PROJECT_ID" --name="$PROJECT_NAME"; fi
gcloud config set project "$PROJECT_ID"

step "billing link"
linked="$(gcloud billing projects describe "$PROJECT_ID" --format='value(billingAccountName)')"
if [ "$linked" = "billingAccounts/$BILLING_ACCOUNT" ]; then ok "linked to $BILLING_ACCOUNT"
else gcloud billing projects link "$PROJECT_ID" --billing-account="$BILLING_ACCOUNT"; fi

step "budget ${BUDGET_AMOUNT}${BUDGET_CURRENCY}"
gcloud services enable billingbudgets.googleapis.com
name="$PROJECT_NAME ${BUDGET_AMOUNT}${BUDGET_CURRENCY}"
if gcloud billing budgets list --billing-account="$BILLING_ACCOUNT" --format='value(displayName)' | grep -qxF "$name"; then
  ok "exists"
else
  # Alerts by email to billing admins. A budget notifies; it never stops spend.
  gcloud billing budgets create \
    --billing-account="$BILLING_ACCOUNT" \
    --display-name="$name" \
    --budget-amount="${BUDGET_AMOUNT}${BUDGET_CURRENCY}" \
    --filter-projects="projects/$PROJECT_ID" \
    --threshold-rule=percent=0.5 \
    --threshold-rule=percent=0.9 \
    --threshold-rule=percent=1.0 \
    --threshold-rule=percent=1.0,basis=forecasted-spend
fi
