# Copyright 2020 Odoo Community Association (OCA)
# Copyright 2020 Opener B.V. <stefan@opener.am>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from openupgradelib import openupgrade

from odoo import tools

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.openupgrade_scripts.apriori import merged_modules, renamed_modules
except ImportError:
    renamed_modules = {}
    merged_modules = {}
    _logger.warning(
        "You are using openupgrade_framework without having"
        " openupgrade_scripts module available."
        " The upgrade process will not work properly."
    )


module_category_xmlid_renames = [
    # Module category renames were not detected by the analyze. These records
    # are created on the fly when intializing a new database in
    # odoo/modules/db.py
    (
        "base.module_category_accounting_expenses",
        "base.module_category_human_resources_expenses",
    ),
    ("base.module_category_discuss", "base.module_category_productivity_discuss"),
    (
        "base.module_category_localization_account_charts",
        "base.module_category_accounting_localizations_account_charts",
    ),
    ("base.module_category_marketing_survey", "base.module_category_marketing_surveys"),
    (
        "base.module_category_operations_helpdesk",
        "base.module_category_services_helpdesk",
    ),
    (
        "base.module_category_operations_inventory",
        "base.module_category_inventory_inventory",
    ),
    (
        "base.module_category_operations_inventory_delivery",
        "base.module_category_inventory_delivery",
    ),
    (
        "base.module_category_operations_maintenance",
        "base.module_category_manufacturing_maintenance",
    ),
    (
        "base.module_category_operations_project",
        "base.module_category_services_project",
    ),
    (
        "base.module_category_operations_purchase",
        "base.module_category_inventory_purchase",
    ),
    (
        "base.module_category_operations_timesheets",
        "base.module_category_services_timesheets",
    ),
]


@openupgrade.migrate(use_env=False)
def migrate(cr, version):
    """
    Don't request an env for the base pre migration as flushing the env in
    odoo/modules/registry.py will break on the 'base' module not yet having
    been instantiated.
    """
    if "openupgrade_framework" not in tools.config["server_wide_modules"]:
        logging.error(
            "openupgrade_framework is not preloaded. You are highly "
            "recommended to run the Odoo with --load=openupgrade_framework "
            "when migrating your database."
        )
    # Rename xmlids of module categies with allow_merge
    openupgrade.rename_xmlids(cr, module_category_xmlid_renames, allow_merge=True)
    # Update ir_model_data timestamps from obsolete columns
    openupgrade.logged_query(
        cr,
        """
        UPDATE ir_model_data
        SET create_date = COALESCE(date_init, create_date),
            write_date = COALESCE(date_update, write_date)
        WHERE (create_date IS NULL OR write_date IS NULL) AND
            (date_init IS NOT NULL OR date_update IS NOT NULL)
        """,
    )
    # Set default values from odoo/addons/base/data/base_data.sql
    cr.execute(
        """ ALTER TABLE ir_model_data
        ALTER COLUMN create_date
        SET DEFAULT NOW() AT TIME ZONE 'UTC',
        ALTER COLUMN write_date
        SET DEFAULT NOW() AT TIME ZONE 'UTC'
    """
    )
    # Perform module renames and merges
    openupgrade.update_module_names(cr, renamed_modules.items())
    openupgrade.update_module_names(cr, merged_modules.items(), merge_modules=True)
    # Migrate partners from Fil to Tagalog
    # See https://github.com/odoo/odoo/commit/194ed76c5cc9
    openupgrade.logged_query(
        cr, "UPDATE res_partner SET lang = 'tl_PH' WHERE lang = 'fil_PH'"
    )
