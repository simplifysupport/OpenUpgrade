# Copyright 2021 ForgeFlow S.L.  <https://www.forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

from odoo.tools.translate import _


def fill_account_journal_posted_before(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move
        SET posted_before = TRUE
        WHERE state = 'posted'""",
    )


def fill_code_prefix_end_field(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_group
        SET code_prefix_end = code_prefix_start
        """,
    )


def fill_default_account_id_field(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_journal
        SET default_account_id = {0}
        WHERE {0} = {1} OR ({0} IS NOT NULL AND {1} IS NULL);
        UPDATE account_journal
        SET default_account_id = {1}
        WHERE {0} IS NULL AND {1} IS NOT NULL
        """.format(
            openupgrade.get_legacy_name("default_credit_account_id"),
            openupgrade.get_legacy_name("default_debit_account_id"),
        ),
    )


def fill_payment_id_and_statement_line_id_fields(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move_line aml
        SET payment_id = am.payment_id
        FROM account_move am
        WHERE am.id = aml.move_id AND am.payment_id IS NOT NULL
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move_line aml
        SET statement_line_id = am.statement_line_id
        FROM account_move am
        WHERE am.id = aml.move_id AND am.statement_line_id IS NOT NULL
        """,
    )


def create_account_reconcile_model_lines(env):
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_reconcile_model_line (model_id, company_id,
            sequence, account_id, journal_id, label, amount_type,
            force_tax_included, amount, amount_string, analytic_account_id,
            create_uid, create_date, write_uid, write_date)
        SELECT id, company_id, sequence, account_id, journal_id, label,
            amount_type, force_tax_included,
            CASE WHEN amount_type = 'regex' THEN 0 ELSE amount END as amount,
            CASE WHEN amount_type = 'regex' THEN amount_from_label_regex
                ELSE amount || '' END as amount_string,
            analytic_account_id, create_uid, create_date, write_uid, write_date
        FROM (
            SELECT arm.* FROM account_reconcile_model arm
            LEFT JOIN ir_model_data imd ON (
                imd.model = 'account.reconcile.model' AND imd.res_id = arm.id)
            WHERE imd.id IS NULL) arm1
        WHERE rule_type != 'invoice_matching' OR (rule_type = 'invoice_matching'
            AND match_total_amount AND match_total_amount_param < 100.0)
        UNION ALL
        SELECT id, company_id, sequence, second_account_id, second_journal_id,
            second_label, second_amount_type, force_second_tax_included,
            CASE WHEN second_amount_type = 'regex' THEN 0
                ELSE second_amount END as amount,
            CASE WHEN second_amount_type = 'regex' THEN second_amount_from_label_regex
                ELSE second_amount || '' END as amount_string,
            second_analytic_account_id, create_uid, create_date, write_uid, write_date
        FROM (
            SELECT arm.* FROM account_reconcile_model arm
            LEFT JOIN ir_model_data imd ON (
                imd.model = 'account.reconcile.model' AND imd.res_id = arm.id)
            WHERE imd.id IS NULL) arm2
        WHERE has_second_line AND (rule_type != 'invoice_matching' OR (
            rule_type = 'invoice_matching' AND match_total_amount
            AND match_total_amount_param < 100.0))
        ORDER BY id""",
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_reconcile_model_analytic_tag_rel rel
        SET account_reconcile_model_line_id = arml.id
        FROM account_reconcile_model_line arml
        WHERE arml.model_id = rel.account_reconcile_model_id""",
    )
    openupgrade.logged_query(
        env.cr,
        """
        DELETE FROM account_reconcile_model_analytic_tag_rel
        WHERE account_reconcile_model_line_id IS NULL""",
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_reconcile_model_analytic_tag_rel (
            account_reconcile_model_line_id, account_analytic_tag_id)
        SELECT arml.id, rel.account_analytic_tag_id
        FROM account_reconcile_model_second_analytic_tag_rel rel
        JOIN account_reconcile_model_line arml
            ON rel.account_reconcile_model_id = arml.model_id""",
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_reconcile_model_line_account_tax_rel (
            account_reconcile_model_line_id, account_tax_id)
        SELECT arml.id, rel.account_tax_id
        FROM account_reconcile_model_account_tax_rel rel
        JOIN account_reconcile_model_line arml
            ON rel.account_reconcile_model_id = arml.model_id""",
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_reconcile_model_line_account_tax_rel (
            account_reconcile_model_line_id, account_tax_id)
        SELECT arml.id, rel.account_tax_id
        FROM account_reconcile_model_account_tax_bis_rel rel
        JOIN account_reconcile_model_line arml
            ON rel.account_reconcile_model_id = arml.model_id""",
    )


def create_account_reconcile_model_template_lines(env):
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_reconcile_model_line_template (model_id,
            sequence, account_id, label, amount_type,
            force_tax_included, amount_string,
            create_uid, create_date, write_uid, write_date)
        SELECT id, sequence, account_id, label,
            amount_type, force_tax_included,
            CASE WHEN amount_type = 'regex' THEN amount_from_label_regex
                ELSE amount || '' END as amount_string,
            create_uid, create_date, write_uid, write_date
        FROM (
            SELECT armt.* FROM account_reconcile_model_template armt
            LEFT JOIN ir_model_data imd ON (
                imd.model = 'account.reconcile.model.template'
                    AND imd.res_id = armt.id)
            WHERE imd.id IS NULL) armt1
        WHERE rule_type != 'invoice_matching' OR (rule_type = 'invoice_matching'
            AND match_total_amount AND match_total_amount_param < 100.0)
        UNION ALL
        SELECT id, sequence, second_account_id,
            second_label, second_amount_type, force_second_tax_included,
            CASE WHEN second_amount_type = 'regex' THEN second_amount_from_label_regex
                ELSE second_amount || '' END as amount_string,
            create_uid, create_date, write_uid, write_date
        FROM (
            SELECT armt.* FROM account_reconcile_model_template armt
            LEFT JOIN ir_model_data imd ON (
                imd.model = 'account.reconcile.model.template'
                    AND imd.res_id = armt.id)
            WHERE imd.id IS NULL) armt2
        WHERE has_second_line AND (rule_type != 'invoice_matching' OR (
            rule_type = 'invoice_matching' AND match_total_amount
            AND match_total_amount_param < 100.0))
        ORDER BY id""",
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_reconcile_model_line_template_account_tax_template_rel (
            account_reconcile_model_line_template_id, account_tax_template_id)
        SELECT armlt.id, rel.account_tax_template_id
        FROM account_reconcile_model_template_account_tax_template_rel rel
        JOIN account_reconcile_model_line_template armlt
            ON rel.account_reconcile_model_template_id = armlt.model_id""",
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_reconcile_model_line_template_account_tax_template_rel (
            account_reconcile_model_line_template_id, account_tax_template_id)
        SELECT armlt.id, rel.account_tax_template_id
        FROM account_reconcile_model_tmpl_account_tax_bis_rel rel
        JOIN account_reconcile_model_line_template armlt
            ON rel.account_reconcile_model_template_id = armlt.model_id""",
    )


def create_account_tax_report_lines(env):
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE account_tax_report
        ADD COLUMN root_line_id integer""",
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_tax_report (name, country_id, root_line_id,
            create_uid, create_date, write_uid, write_date)
        SELECT name, country_id, id, create_uid, create_date, write_uid, write_date
        FROM account_tax_report_line
        WHERE parent_id IS NULL
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_tax_report_line atrl
        SET report_id = atr.id
        FROM account_tax_report atr
        WHERE atr.root_line_id = atrl.id
        """,
    )
    while True:
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE account_tax_report_line atrl
            SET report_id = atrl2.report_id
            FROM account_tax_report_line atrl2
            WHERE atrl.parent_id = atrl2.id AND atrl.report_id IS NULL
            RETURNING atrl.id""",
        )
        if not env.cr.fetchone():
            break


def post_statements_with_unreconciled_lines(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_bank_statement bst
        SET state = 'posted'
        FROM account_bank_statement_line bstl
        WHERE bst.state = 'confirm' AND bstl.statement_id = bst.id
            AND bstl.is_reconciled IS DISTINCT FROM TRUE
        """,
    )


def pass_bank_statement_line_note_to_journal_entry_narration(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET narration = CASE
            WHEN char_length(COALESCE(am.narration, '')) = 0 THEN absl.note
            ELSE am.narration || ' ' || absl.note END
        FROM account_bank_statement_line absl
        WHERE absl.move_id = am.id AND char_length(COALESCE(absl.note, '')) > 0
        """,
    )


def pass_payment_to_journal_entry_narration(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET narration = CASE
            WHEN char_length(COALESCE(am.narration, '')) = 0 THEN ap.communication
            ELSE am.narration || ' ' || ap.communication END
        FROM account_payment ap
        WHERE ap.move_id = am.id AND char_length(COALESCE(ap.communication, '')) > 0
        """,
    )


def fill_company_account_cash_basis_base_account_id(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_chart_template chart
        SET property_cash_basis_base_account_id = att.cash_basis_base_account_id
        FROM account_tax_template att
        WHERE att.chart_template_id = chart.id
            AND att.cash_basis_base_account_id IS NOT NULL
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE res_company rc
        SET account_cash_basis_base_account_id = at.cash_basis_base_account_id
        FROM account_tax at
        WHERE at.company_id = rc.id
            AND at.cash_basis_base_account_id IS NOT NULL
        """,
    )


def fix_group_company_and_create_groups_for_each_company_if_necessary(env):
    def _get_all_ordered_children(groups):
        children = groups
        for child_group in groups:
            group_childs = env["account.group"].search(
                [("parent_id", "in", child_group.ids)]
            )
            if group_childs:
                children |= _get_all_ordered_children(group_childs)
        return children

    all_parent_groups = env["account.group"].search([("parent_id", "=", False)])
    compute_parent_path = False
    for parent_group in all_parent_groups:
        group_plus_childs = _get_all_ordered_children(parent_group)
        accounts = env["account.account"].search(
            [("group_id", "in", group_plus_childs.ids)]
        )
        companies = accounts.mapped("company_id")
        if len(companies) == 1:
            group_plus_childs.filtered(lambda g: g.company_id != companies).write(
                {"company_id": companies.id}
            )
        elif len(companies) > 1:
            compute_parent_path = True
            companies = companies.sorted()
            relation_dict = {}
            for company in companies:
                relation_dict[company.id] = {}
                if company == companies[0]:
                    for group in group_plus_childs:
                        relation_dict[company.id][group.id] = group
                    group_plus_childs.filtered(lambda g: g.company_id != company).write(
                        {"company_id": company.id}
                    )
                    continue
                for group in group_plus_childs:
                    # doing query to avoid "adapt" redirection methods in "create"
                    # method of account groups. This way, we have more control of
                    # everything instead of delegating to odoo.
                    env.cr.execute(
                        """
                    INSERT INTO account_group (parent_id, parent_path, name,
                        code_prefix_start, code_prefix_end, company_id,
                        create_uid, write_uid, create_date, write_date)
                    SELECT {parent_id}, parent_path, name, code_prefix_start,
                        code_prefix_end, {company_id}, create_uid,
                        write_uid, create_date, write_date
                    FROM account_group
                    WHERE id = {id}
                    RETURNING id
                    """.format(
                            id=group.id,
                            company_id=company.id,
                            parent_id=group.parent_id
                            and relation_dict[company.id][group.parent_id.id].id
                            or "NULL",
                        )
                    )
                    new_group = env["account.group"].browse(env.cr.fetchone())
                    relation_dict[company.id][group.id] = new_group
            for account in accounts.filtered(
                lambda a: a.group_id != relation_dict[a.company_id.id][a.group_id.id]
            ):
                account.group_id = relation_dict[account.company_id.id][
                    account.group_id.id
                ]
    if compute_parent_path:
        env["account.group"]._parent_store_compute()


def fill_company_account_journal_suspense_account_id(env):
    companies = env["res.company"].search([("chart_template_id", "!=", False)])
    for company in companies:
        chart = company.chart_template_id
        account = chart._create_liquidity_journal_suspense_account(
            company, chart.code_digits
        )
        company.account_journal_suspense_account_id = account
    journals = env["account.journal"].search(
        [("type", "in", ("bank", "cash")), ("company_id", "in", companies.ids)]
    )
    journals._compute_suspense_account_id()


def fill_account_journal_payment_credit_debit_account_id(env):
    journals = env["account.journal"].search([("type", "in", ("bank", "cash"))])
    current_assets_type = env.ref("account.data_account_type_current_assets")
    for journal in journals:
        random_account = env["account.account"].search(
            [("company_id", "=", journal.company_id.id)], limit=1
        )
        digits = len(random_account.code) if random_account else 6
        if journal.type == "bank":
            liquidity_account_prefix = journal.company_id.bank_account_code_prefix or ""
        else:
            liquidity_account_prefix = (
                journal.company_id.cash_account_code_prefix
                or journal.company_id.bank_account_code_prefix
                or ""
            )
        journal.payment_debit_account_id = env["account.account"].create(
            {
                "name": _("Outstanding Receipts"),
                "code": env["account.account"]._search_new_account_code(
                    journal.company_id, digits, liquidity_account_prefix
                ),
                "reconcile": True,
                "user_type_id": current_assets_type.id,
                "company_id": journal.company_id.id,
            }
        )
        journal.payment_credit_account_id = (
            env["account.account"]
            .create(
                {
                    "name": _("Outstanding Payments"),
                    "code": env["account.account"]._search_new_account_code(
                        journal.company_id, digits, liquidity_account_prefix
                    ),
                    "reconcile": True,
                    "user_type_id": current_assets_type.id,
                    "company_id": journal.company_id.id,
                }
            )
            .id
        )


def try_delete_noupdate_records(env):
    openupgrade.delete_records_safely_by_xml_id(
        env,
        [
            "account.sequence_payment_customer_invoice",
            "account.sequence_payment_customer_refund",
            "account.sequence_payment_supplier_invoice",
            "account.sequence_payment_supplier_refund",
            "account.sequence_payment_transfer",
        ],
    )


@openupgrade.migrate()
def migrate(env, version):
    fill_account_journal_posted_before(env)
    fill_code_prefix_end_field(env)
    fill_default_account_id_field(env)
    fill_payment_id_and_statement_line_id_fields(env)
    create_account_reconcile_model_lines(env)
    create_account_reconcile_model_template_lines(env)
    create_account_tax_report_lines(env)
    post_statements_with_unreconciled_lines(env)
    pass_bank_statement_line_note_to_journal_entry_narration(env)
    pass_payment_to_journal_entry_narration(env)
    fill_company_account_cash_basis_base_account_id(env)
    openupgrade.load_data(env.cr, "account", "14.0.1.1/noupdate_changes.xml")
    try_delete_noupdate_records(env)
    fix_group_company_and_create_groups_for_each_company_if_necessary(env)
    fill_company_account_journal_suspense_account_id(env)
    fill_account_journal_payment_credit_debit_account_id(env)
    openupgrade.delete_record_translations(
        env.cr,
        "account",
        ["email_template_edi_invoice", "mail_template_data_payment_receipt"],
    )
