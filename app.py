from decimal import Decimal, ROUND_HALF_UP
from datetime import date

import pandas as pd
import streamlit as st
import database

from database import (
    add_expense,
    delete_expense,
    get_expenses,
    init_database,
    update_expense,
)

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💶",
    layout="wide",
)



demo_mode = st.sidebar.toggle("Use demo database", value=False)

database.DB_PATH = (
    database.Path(__file__).resolve().parent
    / "data"
    / ("demo_expenses.db" if demo_mode else "expenses.db")
)

if demo_mode:
    st.sidebar.info(
        "Demo mode: fictional data in a separate database."
    )



init_database()
if "success_message" in st.session_state:
    st.success(st.session_state.pop("success_message"))

st.title("Expense Tracker")
st.write("Track your expenses and understand your spending.")

with st.form("expense_form", clear_on_submit=True):
    expense_date = st.date_input("Date")
    amount = st.number_input(
        "Amount (€)",
        min_value=0.01,
        value=1.00,
        step=0.50,
        format="%.2f",
    )
    category = st.selectbox(
        "Category",
        [
            "Food",
            "Transport",
            "Housing",
            "Bills",
            "Health",
            "Entertainment",
            "Other",
        ],
    )
    description = st.text_input("Description", max_chars=200)

    submitted = st.form_submit_button("Add expense")

if submitted:
    amount_cents = int(
        (Decimal(str(amount)) * 100).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )

    try:
        add_expense(
            expense_date.isoformat(),
            amount_cents,
            category,
            description.strip(),
        )
    except Exception:
        st.error("The expense could not be saved. Please try again.")
    else:
        st.success("Expense saved successfully.")

st.divider()
st.subheader("Saved expenses")

expenses = get_expenses()

if not expenses:
    st.info("No expenses yet. Add your first expense above.")
else:
    df = pd.DataFrame(expenses)
    df["month"] = df["expense_date"].str[:7]

    col1, col2 = st.columns(2)

    with col1:
        selected_month = st.selectbox(
            "Month",
            ["All months"] + sorted(
                df["month"].unique().tolist(),
                reverse=True,
            ),
        )

    with col2:
        selected_category = st.selectbox(
            "Filter by category",
            ["All categories"] + sorted(
                df["category"].unique().tolist()
            ),
        )

    filtered_df = df.copy()

    if selected_month != "All months":
        filtered_df = filtered_df[
            filtered_df["month"] == selected_month
        ]

    if selected_category != "All categories":
        filtered_df = filtered_df[
            filtered_df["category"] == selected_category
        ]

    total_cents = int(filtered_df["amount_cents"].sum())

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total expenses", f"€{total_cents / 100:,.2f}")

    with col2:
        st.metric("Number of expenses", len(filtered_df))

    if filtered_df.empty:
        st.info("No expenses match the selected filters.")
    else:
        display_df = filtered_df.rename(
            columns={
                "expense_date": "Date",
                "category": "Category",
                "description": "Description",
            }
        ).copy()

        display_df["Amount (€)"] = (
            display_df["amount_cents"] / 100
        )

        table = display_df[
            ["Date", "Amount (€)", "Category", "Description"]
        ]

        st.dataframe(table, hide_index=True)

        st.subheader("Spending by category")

        category_totals = (
            filtered_df.groupby("category")["amount_cents"]
            .sum()
            .div(100)
            .rename("Amount (€)")
        )

        st.bar_chart(category_totals)

        # Neutralise spreadsheet formula prefixes in user-entered text.
        export_table = table.copy()

        def safe_csv_text(value):
            text = str(value)
            if text.lstrip().startswith(("=", "+", "-", "@")):
                return "'" + text
            return text

        export_table["Description"] = (
            export_table["Description"].map(safe_csv_text)
        )

        csv = export_table.to_csv(
            index=False,
            float_format="%.2f",
        ).encode("utf-8-sig")

        st.download_button(
            label="Download filtered expenses as CSV",
            data=csv,
            file_name="expenses.csv",
            mime="text/csv",
        )

        st.divider()
st.subheader("Delete an expense")

delete_options = {
    int(expense["id"]): (
        f"#{expense['id']} | {expense['expense_date']} | "
        f"€{expense['amount_cents'] / 100:.2f} | "
        f"{expense['category']} | {expense['description']}"
    )
    for expense in expenses
}

if delete_options:
    with st.form("delete_expense_form"):
        selected_id = st.selectbox(
            "Select an expense to delete",
            options=list(delete_options),
            format_func=lambda expense_id: delete_options[expense_id],
        )

        confirmed = st.checkbox(
            "I confirm that I want to permanently delete this expense."
        )

        delete_submitted = st.form_submit_button("Delete expense")

    if delete_submitted:
        if not confirmed:
            st.warning("Please confirm the deletion first.")
        else:
            try:
                deleted = delete_expense(selected_id)
            except Exception:
                st.error("The expense could not be deleted. Please try again.")
            else:
                if deleted:
                    st.session_state["success_message"] = (
                        "Expense deleted successfully."
                    )
                    st.rerun()
                else:
                    st.warning(
                        "This expense no longer exists. Refresh the page."
                    )
else:
    st.info("There are no expenses to delete.")


st.divider()
st.subheader("Edit an expense")

if expenses:
    expense_lookup = {
        int(expense["id"]): expense
        for expense in expenses
    }

    selected_edit_id = st.selectbox(
        "Select an expense to edit",
        options=list(expense_lookup),
        format_func=lambda expense_id: (
            f"#{expense_id} | "
            f"{expense_lookup[expense_id]['expense_date']} | "
            f"€{expense_lookup[expense_id]['amount_cents'] / 100:.2f} | "
            f"{expense_lookup[expense_id]['category']}"
        ),
        key="edit_expense_selector",
    )

    selected_expense = expense_lookup[selected_edit_id]

    categories = [
        "Food",
        "Transport",
        "Housing",
        "Bills",
        "Health",
        "Entertainment",
        "Other",
    ]

    # Preserve existing categories if the list changes later.
    if selected_expense["category"] not in categories:
        categories.append(selected_expense["category"])

    with st.form(f"edit_expense_form_{selected_edit_id}"):
        edited_date = st.date_input(
            "Date",
            value=date.fromisoformat(
                selected_expense["expense_date"]
            ),
        )

        edited_amount = st.number_input(
            "Amount (€)",
            min_value=0.01,
            value=selected_expense["amount_cents"] / 100,
            step=0.50,
            format="%.2f",
        )

        edited_category = st.selectbox(
            "Category",
            options=categories,
            index=categories.index(
                selected_expense["category"]
            ),
        )

        edited_description = st.text_input(
            "Description",
            value=selected_expense["description"],
            max_chars=200,
        )

        save_changes = st.form_submit_button("Save changes")

    if save_changes:
        edited_cents = int(
            (Decimal(str(edited_amount)) * 100).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP,
            )
        )

        try:
            updated = update_expense(
                selected_edit_id,
                edited_date.isoformat(),
                edited_cents,
                edited_category,
                edited_description.strip(),
            )
        except Exception:
            st.error(
                "The expense could not be updated. Please try again."
            )
        else:
            if updated:
                st.session_state["success_message"] = (
                    "Expense updated successfully."
                )
                st.rerun()
            else:
                st.warning(
                    "This expense no longer exists. Refresh the page."
                )
else:
    st.info("There are no expenses to edit.")