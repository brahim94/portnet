# -*- coding: utf-8 -*-

{
    "name": "Purchase Request Extension",
    "author": "Warlock Technologies",
    "description": """Purchase Request Extension""",
    "summary": """Purchase Request Extension""",
    "version": "13.0.3.22.3",
    "support": "info@warlocktechnologies.com",
    "website": "http://warlocktechnologies.com",
    "license": "LGPL-3",
    "category": "Purchase",
    "depends": ["base", "purchase_request", "purchase_request_department", "purchase_requisition", "resource"],
    "data": [
        "security/purchase_request.xml",
        "security/market_execution.xml",
        "security/ir.model.access.csv",
        "data/purchase_requisition_data.xml",
        "wizard/submission_date_increment_wizard.xml",
        "wizard/purchase_req_line_wizard.xml",
        "views/purchase_request_view.xml",
        "views/purchase_request_line_view.xml",
        "views/purchase_requisition_type.xml",
        "views/purchase_requisition.xml",
        "views/purchase_order_view.xml",
        "views/market_execution_view.xml",
        "views/resource_calendar_view.xml",
    ],
    "demo": [  
    ],
    "installable": True,
}
