# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning, RedirectWarning
import time, datetime

class Tenant(models.Model):
    _name = 'apartment.tenant'

    parnert_id = fields.Many2one('res.partner', "Khách hàng", required = True)
    contract_id = fields.Many2one('apartment.contract', 'Hợp đồng', required = True)
    date_start = fields.Date('Ngày bắt đầu', required = True)
    date_end = fields.Date('Ngày kết thúc')

