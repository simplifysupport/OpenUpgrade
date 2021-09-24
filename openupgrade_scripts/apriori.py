""" Encode any known changes to the database here
to help the matching process
"""

# Renamed modules is a mapping from old module name to new module name
renamed_modules = {
    # odoo
    "account_facturx": "account_edi_facturx",
    "sale_coupon": "coupon",
    "website_rating": "portal_rating",
    # OCA/account-invoice-reporting
    "account_invoice_comment_template": "account_comment_template",
    # OCA/edi
    "edi": "edi_oca",
    "edi_account": "edi_account_oca",
    "edi_exchange_template": "edi_exchange_template_oca",
    "edi_storage": "edi_storage_oca",
    "edi_webservice": "edi_webservice_oca",
    "edi_xml": "edi_xml_oca",
    # OCA/server-tools
    "openupgrade_records": "upgrade_analysis",
    # OCA/manufacture
    "mrp_production_request": "mrp_request",
    # OCA/...
}

# Merged modules contain a mapping from old module names to other,
# preexisting module names
merged_modules = {
    # odoo
    "account_analytic_default": "account",
    "account_analytic_default_hr_expense": "hr_expense",
    "account_analytic_default_purchase": "purchase",
    "hr_expense_check": "hr_expense",
    "hr_holidays_calendar": "hr_holidays",
    "hw_proxy": "hw_drivers",
    "l10n_cn_small_business": "l10n_cn",
    "partner_autocomplete_address_extended": "base_address_extended",
    "payment_stripe_checkout_webhook": "payment_stripe",
    "pos_cash_rounding": "point_of_sale",
    "pos_kitchen_printer": "pos_restaurant",
    "pos_reprint": "point_of_sale",
    "website_theme_install": "website",
    # OCA/partner-contact
    "partner_bank_active": "base",
    # OCA/stock-logistics-warehouse
    "stock_inventory_include_exhausted": "stock",
    # OCA/...
}

# only used here for upgrade_analysis
renamed_models = {
    # odoo
<<<<<<< HEAD
    "crm.lead.tag": "crm.tag",
    "email_template.preview": "mail.template.preview",
    "event.answer": "event.question.answer",
    "product.style": "product.ribbon",
    "report.sale_coupon.report_coupon": "report.coupon.report_coupon",
    "sale.coupon": "coupon.coupon",
    "sale.coupon.generate": "coupon.generate.wizard",
    "sale.coupon.program": "coupon.program",
    "sale.coupon.reward": "coupon.reward",
    "sale.coupon.rule": "coupon.rule",
    "survey.user_input_line": "survey.user_input.line",
    "survey.label": "survey.question.answer",
    # OCA/server-tools
    "openupgrade.analysis.wizard": "upgrade.analysis",
    "openupgrade.attribute": "upgrade.attribute",
    "openupgrade.comparison.config": "upgrade.comparison.config",
    "openupgrade.record": "upgrade.record",
    "openupgrade.generate.records.wizard": "upgrade.generate.record.wizard",
    "openupgrade.install.all.wizard": "upgrade.install.wizard",
=======
    # OCA/manufacture
    "mrp.production.request": "mrp.request",
    "mrp.production.request.create.mo": "mrp.request.create.mo",
    "mrp.production.request.create.mo.line": "mrp.request.create.mo.line",
>>>>>>> ceea217ce13a9eb79775cf77bd797e3df422836b
}

# only used here for upgrade_analysis
merged_models = {}
