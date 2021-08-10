# Copyright 2021 ForgeFlow S.L.  <https://www.forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def rename_fields(env):
    openupgrade.rename_fields(
        env,
        [
            (
                "account.bank.statement.line",
                "account_bank_statement_line",
                "name",
                "payment_ref",
            ),
            (
                "account.bank.statement.line",
                "account_bank_statement_line",
                "currency_id",
                "foreign_currency_id",
            ),
            (
                "account.bank.statement.line",
                "account_bank_statement_line",
                "journal_currency_id",
                "currency_id",
            ),
            (
                "account.cash.rounding",
                "account_cash_rounding",
                "account_id",
                "profit_account_id",
            ),
            (
                "account.group",
                "account_group",
                "code_prefix",
                "code_prefix_start",
            ),
            (
                "account.move",
                "account_move",
                "invoice_partner_bank_id",
                "partner_bank_id",
            ),
            (
                "account.move",
                "account_move",
                "invoice_payment_ref",
                "payment_reference",
            ),
            (
                "account.move",
                "account_move",
                "invoice_sent",
                "is_move_sent",
            ),
            (
                "account.move",
                "account_move",
                "type",
                "move_type",
            ),
            (
                "account.move",
                "account_move",
                "invoice_payment_state",
                "payment_state",
            ),
            (
                "account.move.line",
                "account_move_line",
                "tag_ids",
                "tax_tag_ids",
            ),
            (
                "res.company",
                "res_company",
                "account_onboarding_sample_invoice_state",
                "account_onboarding_create_invoice_state",
            ),
            (
                "res.company",
                "res_company",
                "accrual_default_journal_id",
                "automatic_entry_default_journal_id",
            ),
        ],
    )


def m2m_tables_account_journal_renamed(env):
    openupgrade.rename_tables(
        env.cr,
        [
            ("account_account_type_rel", "journal_account_control_rel"),
            ("account_journal_type_rel", "journal_account_type_control_rel"),
        ],
    )


def remove_constrains_reconcile_models(env):
    openupgrade.remove_tables_fks(
        env.cr,
        [
            "account_reconcile_model_analytic_tag_rel",
            "account_reconcile_model_account_tax_rel",
            "account_reconcile_model_template_account_tax_template_rel",
            "account_reconcile_model_tmpl_account_tax_bis_rel",
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE account_reconcile_model_analytic_tag_rel
        ALTER COLUMN account_reconcile_model_id DROP NOT NULL
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE account_reconcile_model_analytic_tag_rel
        ADD COLUMN account_reconcile_model_line_id integer
        """,
    )


def copy_fields(env):
    openupgrade.rename_columns(
        env.cr,
        {
            "account_journal": [
                ("default_credit_account_id", None),
                ("default_debit_account_id", None),
            ],
        },
    )
    if openupgrade.column_exists(env.cr, "account_move", "move_type"):
        # see account_tax_balance of OCA
        openupgrade.rename_columns(
            env.cr,
            {
                "account_move": [
                    ("move_type", None),
                ],
            },
        )


def add_move_id_field_account_bank_statement_line(env):
    if not openupgrade.column_exists(
        env.cr, "account_bank_statement_line", "currency_id"
    ):
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE account_bank_statement_line
            ADD COLUMN currency_id integer
            """,
        )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_bank_statement_line absl
        SET currency_id = COALESCE(aj.currency_id, rc.currency_id)
        FROM account_bank_statement bs
        JOIN account_journal aj ON bs.journal_id = aj.id
        JOIN res_company rc ON aj.company_id = rc.id
        WHERE absl.statement_id = bs.id
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE account_bank_statement_line
        ADD COLUMN move_id integer
        """,
    )
    if not openupgrade.column_exists(env.cr, "account_move", "statement_line_id"):
        # In v10 existed that field
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE account_move
            ADD COLUMN statement_line_id integer
            """,
        )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET statement_line_id = aml.statement_line_id
        FROM account_move_line aml
        WHERE aml.move_id = am.id AND aml.statement_line_id IS NOT NULL
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_bank_statement_line absl
        SET move_id = am.id
        FROM account_move am
        WHERE (am.name NOT IN ('', '/') AND (absl.move_name = am.name OR (
            absl.payment_ref = am.name AND absl.move_name IS NULL)))
            OR am.statement_line_id = absl.id
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_bank_statement_line absl
        SET move_id = ap.move_id
        FROM account_payment ap
        WHERE absl.move_id IS NULL AND absl.payment_ref NOT IN ('', '/')
            AND absl.payment_ref = ap.communication
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_bank_statement_line absl
        SET move_id = am.id
        FROM account_move am
        WHERE absl.move_id IS NULL AND absl.account_number NOT IN ('', '/')
            AND absl.account_number = am.ref
        """,
    )
    # TODO: if still exist some account_bank_statement_line with null move_id
    # openupgrade.logged_query(
    #     env.cr,
    #     """
    # WITH new_moves AS (
    #     INSERT INTO account_move (statement_line_id, ...
    #         create_uid, create_date, write_uid, write_date)
    #     SELECT id, ...
    #         create_uid, create_date, write_uid, write_date
    #     FROM account_bank_statement_line absl
    #     WHERE absl.move_id IS NULL
    #     RETURNING id, statement_line_id)
    # UPDATE account_bank_statement_line absl
    # SET move_id = am.id
    # FROM new_moves am
    # WHERE absl.id = am.statement_line_id""",
    # )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET statement_line_id = absl.id
        FROM account_bank_statement_line absl
        WHERE am.id = absl.move_id AND am.statement_line_id IS NULL
        """,
    )


def add_move_id_field_account_payment(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_payment ap
        SET currency_id = COALESCE(aj.currency_id, rc.currency_id)
        FROM account_journal aj
        JOIN res_company rc ON aj.company_id = rc.id
        WHERE ap.journal_id = aj.id
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE account_payment
        ADD COLUMN move_id integer
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE account_move
        ADD COLUMN payment_id integer
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET payment_id = aml.payment_id
        FROM account_move_line aml
        WHERE aml.move_id = am.id AND aml.payment_id IS NOT NULL
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_payment ap
        SET move_id = am.id
        FROM account_move am
        WHERE (am.name NOT IN ('', '/') AND (ap.move_name = am.name OR (
            ap.payment_reference = am.name AND ap.move_name IS NULL)))
            OR am.payment_id = ap.id""",
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_payment ap
        SET move_id = am.id
        FROM account_move am
        WHERE ap.move_id IS NULL AND ap.communication NOT IN ('', '/') AND (
            am.payment_reference = ap.communication OR am.ref = ap.communication
            OR am.name = ap.communication)
        """,
    )
    # TODO: if still exist some account_payment with null move_id
    # openupgrade.logged_query(
    #     env.cr,
    #     """
    # WITH new_moves AS (
    #     INSERT INTO account_move (payment_id, ...
    #         create_uid, create_date, write_uid, write_date)
    #     SELECT id, ...
    #         create_uid, create_date, write_uid, write_date
    #     FROM account_payment ap
    #     WHERE ap.move_id IS NULL
    #     RETURNING id, payment_id)
    # UPDATE account_payment ap
    # SET move_id = am.id
    # FROM new_moves am
    # WHERE ao.id = am.payment_id""",
    # )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET payment_id = ap.id
        FROM account_payment ap
        WHERE am.id = ap.move_id
        """,
    )


def fill_empty_partner_type_account_payment(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_payment
        SET partner_type = 'customer'
        WHERE partner_type IS NULL
        """,
    )


def fill_account_move_line_currency_id(env):
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE account_move_line
        DROP CONSTRAINT IF EXISTS account_move_line_check_amount_currency_balance_sign
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move_line
        SET currency_id = company_currency_id
        WHERE currency_id IS NULL
        """,
    )


def fill_account_payment_partner_id(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_payment ap
        SET partner_id = rc.partner_id
        FROM account_journal aj
        JOIN res_company rc ON aj.company_id = rc.id
        WHERE ap.payment_type = 'transfer'
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.set_xml_ids_noupdate_value(
        env, "account", ["account_analytic_line_rule_billing_user"], True
    )
    copy_fields(env)
    rename_fields(env)
    m2m_tables_account_journal_renamed(env)
    remove_constrains_reconcile_models(env)
    add_move_id_field_account_payment(env)
    add_move_id_field_account_bank_statement_line(env)
    fill_empty_partner_type_account_payment(env)
    fill_account_move_line_currency_id(env)
    fill_account_payment_partner_id(env)
