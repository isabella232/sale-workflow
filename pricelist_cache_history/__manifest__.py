# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Pricelist Cache History",
    "summary": "Adds dates to pricelist cache",
    "version": "14.0.1.0.0",
    "category": "Sales",
    "website": "https://github.com/OCA/sale-workflow",
    "author": "Camptocamp SA, Odoo Community Association (OCA)",
    "maintainers": ["mmequignon"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "depends": ["pricelist_cache"],
    "data": [
        "wizards/pricelist_cache_wizard.xml",
        "views/product_pricelist_cache.xml",
    ],
}
