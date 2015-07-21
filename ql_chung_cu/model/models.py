# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning, RedirectWarning
import time, datetime


class ql_chung_cu_toa_nha(models.Model):
    _name = "apartment.building"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char("Tên")


class ql_chung_cu_phong(models.Model):
    _name = "apartment.room"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char("Tên tòa nhà")
    building_id = fields.Many2one('apartment.building', 'Tòa nhà')


class ql_chung_cu_hop_dong(models.Model):
    _name = "apartment.contract"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char('Số hợp đồng', required=True)
    tenent_id = fields.One2many('apartment.tenant', 'contract_id')
    room_id = fields.Many2one('apartment.room', "Phòng", required=True, states={'confirm': [('readonly', True)]})
    price = fields.Float('Đơn giá', states={'confirm': [('readonly', True)]})
    deposit = fields.Float('Số tiền đặt cọc')
    date_created = fields.Date('Ngày tạo hợp đồng')
    date_start = fields.Date('Ngày bắt đầu hợp đồng', required=True, states={'confirm': [('readonly', True)]})
    date_end = fields.Date('Ngày kết thúc hợp đồng')
    water_start = fields.Float('Chỉ số nước ban đầu', required=True, states={'confirm': [('readonly', True)]})
    power_start = fields.Float('Chỉ số điện ban đầu', required=True, states={'confirm': [('readonly', True)]})
    supplier_id = fields.Many2one('res.partner', 'Khách hàng', required=True, states={'confirm': [('readonly', True)]})
    sale_id = fields.One2many('sale.order', 'contract_id', readonly = True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirm', 'Xác nhận'),
        ('cancel', 'Đã hủy')], 'Trạng thái')
    _defaults = {
        'state': 'draft',
        'date_created': time.strftime('%Y-%m-%d')
    }

    @api.one
    def write(self, vals):
        rs = super(ql_chung_cu_hop_dong, self).write(vals)
        if self.date_end != False:
            if self.date_end < self.date_start:
                raise except_orm('Lỗi!',
                                 'Ngày kết thúc hợp đồng không thể nhỏ hơn ngày bắt đầu hợp đồng')
        return rs

    @api.multi
    def create_field(self):
          return {
            'name': 'view_paid_contract',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'paid.contract',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }

    @api.one
    def action_confirm(self):
        pre_month = self.env['apartment.month.index'].search([('room_id', '=', self.room_id.id),
                                                              ('state', '=', 'confirm')],
                                                             order='date desc', limit=1)
        contract_ids = self.search([('room_id', '=', self.room_id.id), ('state', '=', 'confirm')],
                                   order='date_start desc', limit=1)  # get hop dong truoc do
        price = self.env['apartment.price'].search([('id', '!=', 0)], order='id desc', limit=1)
        month = self.env['apartment.month'].search(
            [('year', '=', datetime.datetime.strptime(self.date_start, '%Y-%m-%d').strftime("%Y")),
             ('date_start', '<=', self.date_start), ('date_end', '>=', self.date_start)])
        if contract_ids:
            if (contract_ids.date_end == False):
                raise except_orm('Lỗi!', 'Vui lòng thêm ngày kết thúc vào hợp đồng số %s' % contract_ids.name)
            elif contract_ids.date_end >= self.date_start:
                raise except_orm('Lỗi!',
                                 'Không thể xác nhận 1 hợp đồng có ngày bắt đầu nhỏ hơn hoặc bằng ngày kết thúc của số hợp đồng %s' % contract_ids.name)
            elif (self.date_end != False) and (self.date_end < self.date_start):
                raise except_orm('Lỗi!',
                                 'Ngày kết thúc hợp đồng không thể nhỏ hơn ngày bắt đầu hợp đồng')
            else:
                if pre_month:
                    if (pre_month.water_number < self.water_start or pre_month.power_number < self.power_start):
                        self.env['apartment.month.index'].create({
                            'room_id': self.room_id.id,
                            'water_price': price.water_price,
                            'power_price': price.power_price,
                            'date': self.date_start,
                            'month': month.id,
                            'old_power':pre_month.power_number,
                            'old_water':pre_month.water_number,
                            'water_number': self.water_start,
                            'power_number': self.power_start,
                            'state': 'confirm'
                        })
                        self.state = 'confirm'
                    else:
                        raise except_orm('Lỗi!',
                                         'Chỉ số mới không thể nhỏ hơn chỉ số cũ!' )

        else:
            month = self.env['apartment.month'].search(
                [('year', '=', datetime.datetime.strptime(self.date_start, '%Y-%m-%d').strftime("%Y")),
                 ('date_start', '<=', self.date_start), ('date_end', '>=', self.date_start)])
            pre_month = self.env['apartment.month.index'].search([('room_id', '=', self.room_id.id),
                                                                  ('state', '=', 'confirm')],
                                                                 order='date, id desc', limit=1)
            if pre_month:
                if (pre_month.water_number <= self.water_start or pre_month.power_number <= self.power_start):
                    self.env['apartment.month.index'].create({
                        'room_id': self.room_id.id,
                        'date': self.date_start,
                        'water_price': price.water_price,
                        'power_price': price.power_price,
                        'month': month.id,
                        'old_power':pre_month.power_number,
                        'old_water':pre_month.water_number,
                        'water_number': self.water_start,
                        'power_number': self.power_start,
                        'state': 'confirm'
                    })
                    self.state = 'confirm'
                elif (self.date_end != False) and (self.date_end < self.date_start):
                    raise except_orm('Lỗi!',
                                     'Ngày kết thúc hợp đồng không thể nhỏ hơn ngày bắt đầu hợp đồng')
                else:
                    raise except_orm('Lỗi!',
                                     'Chỉ số mới không thể nhỏ hơn chỉ số cũ!')
            else:
                self.env['apartment.month.index'].create({
                    'room_id': self.room_id.id,
                    'date': self.date_start,
                    'water_price': price.water_price,
                    'power_price': price.power_price,
                    'month': month.id,
                    'water_number': self.water_start,
                    'power_number': self.power_start,
                    'state': 'confirm'
                })
                self.state = 'confirm'

    @api.one
    def action_cancel(self):
        self.state = 'cancel'


class ql_chung_cu_month(models.Model):
    _name = "apartment.month"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char('Tháng', requieqred=True)
    year = fields.Selection([
        ('2015', '2015'),
        ('2016', '2016'),
        ('2017', '2017'),
        ('2018', '2018'),
        ('2019', '2019'),
        ('2020', '2020')], 'Năm', requieqred=True)
    date_start = fields.Date('Ngày bắt đầu')
    date_end = fields.Date('Ngày kết thúc')
    _defaults = {
        'year': datetime.date.today().strftime('%Y')
    }


class ql_chung_cu_dien_nuoc(models.Model):
    _name = "apartment.month.index"
    _order = 'id desc'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(compute='_get_name')
    room_id = fields.Many2one('apartment.room', "Phòng", required=True, states={'draft': [('readonly', False)]})
    date = fields.Date('Ngày ghi chỉ số',readonly = True, required=True, states={'draft': [('readonly', False)]})
    old_water = fields.Float('Chỉ số nước cũ', states={'draft': [('readonly', False)]})
    old_power = fields.Float('Chỉ số điện cũ', states={'draft': [('readonly', False)]})
    water_number = fields.Float("Chỉ số nước mới", required=True, states={'draft': [('readonly', False)]})
    power_number = fields.Float("Chỉ số điện mới", required=True, states={'draft': [('readonly', False)]})
    # month = fields.Many2one("apartment.month", "Tháng", required=True, states={'confirm': [('readonly', True)]})
    power_price = fields.Float("Giá điện", states={'draft': [('readonly', False)]})
    water_price = fields.Float("Giá nước", states={'draft': [('readonly', False)]})
    is_paid = fields.Boolean('Đã thanh toán')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirm', 'Xác nhận'),
        ('paid', 'Đã thanh toán'),
        ('not_paid', 'Không thanh toán'),
        ('cancel', 'Đã hủy')], 'Trạng thái')
    _defaults = {
        'is_paid': False,
    }

    @api.one
    def not_paid(self):
        self.write({
            'state': 'not_paid'
        })

    @api.model
    def create(self, vals):
        cxt = self.env.context
        action = self.env['ir.actions.act_window'].browse(cxt['params']['action'])
        next_month = self.env['apartment.month.index'].search([('room_id', '=', vals['room_id']),
                                                                  ('state', 'not in', ('draft', 'not_paid', 'cancel')),
                                                                  ('date', '>', vals['date'])],
                                                                 order='date asc', limit=1)
        print next_month
        if action.res_model == 'apartment.month.index':
            if (vals['old_water'] > vals['water_number'] or vals['old_power'] > vals['power_number']):
                raise except_orm('Lỗi!', 'Chỉ số mới không thể nhỏ hơn chỉ số cũ')
            elif next_month:
                if (next_month.water_number < vals['water_number'] or next_month.water_number < vals['power_number']):
                    raise except_orm('Lỗi!', 'Chỉ số sau không thể lớn hơn chỉ số trước' )
            return super(ql_chung_cu_dien_nuoc, self).create(vals)
        else:
            return super(ql_chung_cu_dien_nuoc, self).create(vals)

    @api.model
    def default_get(self, fields_list):
        defaults = {
        }
        cxt = self.env.context
        action = self.env['ir.actions.act_window'].browse(cxt['params']['action'])
        price = self.env['apartment.price'].search([('id', '!=', 0)], order='id desc', limit=1)
        if action.res_model == 'apartment.month.index':
            defaults['power_price'] = price.power_price
            defaults['date'] = time.strftime('%Y-%m-%d')
            defaults['water_price'] = price.water_price
            defaults['state'] = 'draft'
        return defaults

    def _get_name(self):
        for record in self:
            record.name = self.room_id.name + ' - ' + self.date

    @api.one
    def action_confirm(self):
        pre_month = self.env['apartment.month.index'].search([('room_id', '=', self.room_id.id),
                                                                  ('state', 'not in', ('draft', 'not_paid', 'cancel')),
                                                                  ('date', '<=', self.date)],
                                                                 order='date desc', limit=1)
        next_month = self.env['apartment.month.index'].search([('room_id', '=', self.room_id.id),
                                                                  ('state', 'not in', ('draft', 'not_paid', 'cancel')),
                                                                  ('date', '>', self.date)],
                                                                 order='date asc', limit=1)
        if pre_month:
            if next_month:
                if pre_month.state=='paid' and next_month.state == 'paid':
                     raise except_orm('Lỗi!', 'Không thể xác nhận phiếu điện nước ở giữa 2 phiếu đã thanh toán' )
        self.state = 'confirm'

    @api.one
    def action_cancel(self):
        self.state = 'cancel'

    @api.onchange('room_id')
    def onchange_service(self):
        if self.room_id:
            pre_month = self.env['apartment.month.index'].search([('room_id', '=', self.room_id.id),
                                                                  ('state', 'not in', ('draft', 'not_paid', 'cancel')),
                                                                  ('date', '<=', self.date)],
                                                                 order='date desc', limit=1)
            if pre_month:
                self.old_water = pre_month.water_number
                self.old_power = pre_month.power_number
            else:
                self.old_water = 0.0
                self.old_power = 0.0

class apartment_price(models.Model):
    _name = 'apartment.price'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    """
        module cấu hình giá điện nước cơ bản
    """

    water_price = fields.Float('Giá nước/m3')
    power_price = fields.Float('Giá điện/Kwh')
class apartment_service_conf(models.Model):
    _name = 'apartment.service.conf'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    """
        module cấu hình các loại dịch vụ cơ bản
    """
    name = fields.Char('Tên dịch vụ')

class apartment_service(models.Model):
    _name = 'apartment.service'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    """
        Module cho phép người dùng nhập dịch vụ sử dụng cho tòa nhà
    """
    name = fields.Char(compute='_get_name')
    room_id = fields.Many2one('apartment.room', "Phòng", required=True)
    date = fields.Date('Ngày ghi dịch vụ', required=True)
    service_type = fields.Many2one('apartment.service.conf', 'Loại dịch vụ', required=True)
    price = fields.Float('Tổng tiền')
    description = fields.Char('Ghi chú')
    is_paid = fields.Boolean('Đã thanh toán')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirm', 'Xác nhận'),
        ('paid', 'Đã thanh toán'),
        ('cancel', 'Đã hủy')], 'Trạng thái')
    _defaults = {
        'state' : 'draft',
        'date' : time.strftime('%Y-%m-%d'),
        'is_paid' : False }

    @api.multi
    def _get_name(self):
        for record in self:
            record.name = self.room_id.name + ' - ' + self.service_type.name

    @api.one
    def action_confirm(self):
        self.state = 'confirm'

    @api.one
    def action_cancel(self):
        self.state = 'cancel'

class PaidContract(models.TransientModel):
    _name = 'paid.contract'

    name = fields.Char('Tên')
    room_id = fields.Many2one('apartment.room', 'Tên phòng', readonly=True)
    supplier_id = fields.Many2one('res.partner', 'Khách hàng', readonly=True)
    month = fields.Many2one("apartment.month", "Tháng", required=True)
    month_id = fields.One2many('apartment.month.index', 'id', string="Điện nước", store=True, readonly=True)
    serivce_id = fields.One2many('apartment.service', 'id', string="Dịch vụ", readonly=True)
    power_amount = fields.Float('Tiền điện', readonly=True)
    water_amount = fields.Float('Tiền nước', readonly=True)
    service_amount = fields.Float('Tiền dịch vụ', readonly=True)
    room_price = fields.Float('Tiền thuê nhà', readonly=True)
    amount_total = fields.Float(string='Tổng tiền', readonly=True)
    contract_id = fields.Many2one('apartment.contract')
    month_line = fields.One2many('paid.contract.line.month', 'contract_id')
    service_line = fields.One2many('paid.contract.line.service', 'contract_id')
    is_load = fields.Boolean()
    is_sale = fields.Boolean()

    @api.one
    def create_so(self):
        sale_id = self.env['sale.order'].create({
        'partner_id': self.contract_id.supplier_id.id,
        'contract_id': self.contract_id.id,
        'note': u"Thanh toán tiền thuê nhà hợp đồng %s"%self.contract_id.name +u" tháng %s" %self.month.name,
        'name': self.contract_id.name + '/' + self.month.name
    })
        power_number = water_number= 0.0
        for order in self:
            for line in order.month_line:
                power_number += line.power_number - line.old_power
                water_number += line.water_number - line.old_water
                line.month_index_ids.write({
                    'is_paid': True,
                    'state': 'paid'
                })
            for line in order.service_line:
                line.service_id.write({
                    'is_paid': True,
                    'state': 'paid'
                })
        price_room = self.env.ref('ql_chung_cu.price_room')
        price_power = self.env.ref('ql_chung_cu.price_power')
        price_water = self.env.ref('ql_chung_cu.price_water')
        price_service = self.env.ref('ql_chung_cu.price_service')
        if self.room_price > 0:
            sale_id.order_line.create({
                'product_id': price_room.id,
                'product_uom_qty': 1,
                'order_id': sale_id.id,
                'name': price_room.name,
                'price_unit': self.room_price
            })
        if self.power_amount > 0:
            sale_id.order_line.create({
                'product_id': price_power.id,
                'product_uom_qty': power_number,
                'order_id': sale_id.id,
                'name': price_power.name,
                'price_unit': self.power_amount/power_number
            })
        if self.water_amount > 0:
            sale_id.order_line.create({
                'product_id': price_water.id,
                'product_uom_qty': water_number,
                'order_id': sale_id.id,
                'name': price_water.name,
                'price_unit': self.water_amount/water_number
            })
        if self.service_amount > 0:
            sale_id.order_line.create({
                'product_id': price_service.id,
                'product_uom_qty': 1,
                'order_id': sale_id.id,
                'name': price_service.name,
                'price_unit': self.service_amount
            })
        self.is_sale = True

    @api.model
    def default_get(self, fields_list):
        defaults = {
        }
        cxt = self.env.context
        if cxt.get('active_model') == 'apartment.contract':
            contract = self.env['apartment.contract'].browse([cxt.get('active_id'),])
            defaults['room_id'] = contract.room_id.id
            defaults['contract_id'] = contract.id
            defaults['supplier_id'] = contract.supplier_id.id
            defaults['is_load'] = False
        return defaults

    @api.one
    def load_info(self):
        contract_id = self.contract_id
        if contract_id.date_end != False:
            service_contract = self.env['apartment.service'].search([('room_id', '=', self.room_id.id),
                                                                       ('date', '<=', contract_id.date_end),
                                                                       ('date', '>=', contract_id.date_start),
                                                                       ('is_paid', '=', False),
                                                                       ('state', '=', 'confirm')],
                                                                        order = 'date desc')
            pw = self.env['apartment.month.index'].search([('room_id', '=', self.room_id.id),
                                                               ('state', 'not in', ('draft', 'not_paid', 'cancel')),
                                                                ('date', '<=', contract_id.date_end),
                                                               ('date', '>=', contract_id.date_start),
                                                                ('is_paid', '=', False)],
                                                                order = 'date desc')
        else:
            service_contract = self.env['apartment.service'].search([('room_id', '=', self.room_id.id),
                                                                    ('is_paid', '=', False),
                                                                    ('date', '>=', contract_id.date_start),
                                                                    ('state', '=', 'confirm')],
                                                                 order = 'date desc')
            pw = self.env['apartment.month.index'].search([('room_id', '=', self.room_id.id),
                                                           ('state', 'not in', ('draft', 'not_paid', 'cancel')),
                                                           ('date', '>=', contract_id.date_start),
                                                           ('is_paid', '=', False)],
                                                         order='date desc')
        for item in pw:
            self.env['paid.contract.line.month'].create({
                'contract_id': self.id,
                'month_index_ids': item.id,
                'room_id': item.room_id.id,
                'date': item.date,
                'old_water': item.old_water,
                'old_power': item.old_power,
                'water_number': item.water_number,
                'power_number': item.power_number,
                'power_price': item.power_price,
                'water_price': item.water_price,

            })
        for item in service_contract:

            self.env['paid.contract.line.service'].create({
                'room_id': item.room_id.id,
                'contract_id': self.id,
                'service_id': item.id,
                'date': item.date,
                'service_type': item.service_type.id,
                'price': item.price,
                'description': item.description
            })
        self.room_price = contract_id.price
        self.write({'is_load': True})
        self.button_dummy()

    @api.multi
    def button_dummy(self):
        for order in self:
            water = val1 = service = power_number = water_number= 0.0
            for line in order.month_line:
                val1 += (line.power_number - line.old_power)*line.power_price
                water += (line.water_number - line.old_water)*line.water_price
            self.power_amount = val1
            self.water_amount = water
            for line in order.service_line:
               service += line.price
            self.service_amount = service
            self.amount_total = self.power_amount + self.water_amount+self.room_price + self.service_amount


class PaidContractOrderLine(models.TransientModel):
    _name = 'paid.contract.line.month'

    contract_id = fields.Many2one('paid.contract', invisible="1")
    month_index_ids = fields.Many2one('apartment.month.index', invisible="1")
    room_id = fields.Many2one('apartment.room', "Phòng", required=True)
    date = fields.Date('Ngày ghi chỉ số', required=True)
    old_water = fields.Float('Chỉ số nước cũ')
    old_power = fields.Float('Chỉ số điện cũ')
    water_number = fields.Float("Chỉ số nước mới", required=True)
    power_number = fields.Float("Chỉ số điện mới", required=True)
    power_price = fields.Float("Giá điện")
    water_price = fields.Float("Giá nước")

    @api.model
    def default_get(self, fields_list):
        defaults = {
        }
        price = self.env['apartment.price'].search([('id', '!=', 0)], order='id desc', limit=1)
        defaults['power_price'] = price.power_price
        defaults['date'] = time.strftime('%Y-%m-%d')
        defaults['water_price'] = price.water_price
        return defaults

    @api.onchange('room_id')
    def onchange_service(self):
        if self.room_id:
            pre_month = self.env['apartment.month.index'].search([('room_id', '=', self.room_id.id),
                                                                  ('state', 'not in', ('draft', 'not_paid', 'cancel')),
                                                                  ('date', '<=', self.date)],
                                                                 order='date desc', limit=1)
            if pre_month:
                self.old_water = pre_month.water_number
                self.old_power = pre_month.power_number
            else:
                self.old_water = 0.0
                self.old_power = 0.0

    @api.model
    def create(self, vals):
        rs =  super(PaidContractOrderLine, self).create(vals)
        month_id = self.env['apartment.month.index'].create({
            'room_id': vals['room_id'],
            'date': vals['date'],
            'old_water': vals['old_water'],
            'old_power': vals['old_power'],
            'power_price': vals['power_price'],
            'water_price': vals['water_price'],
            'water_number': vals['water_number'],
            'power_number': vals['power_number'],

        })

        print month_id
        month_id.action_confirm()
        return rs
    @api.multi
    def write(self, vals):
        raise Warning(self)


class PaidContractServiceLine(models.TransientModel):
    _name = 'paid.contract.line.service'

    room_id = fields.Many2one('apartment.room', "Phòng", required=True)
    contract_id = fields.Many2one('paid.contract', invisible= "1")
    service_id = fields.Many2one('apartment.service', invisible= "1")
    date = fields.Date('Ngày ghi dịch vụ', required=True)
    service_type = fields.Many2one('apartment.service.conf', 'Loại dịch vụ', required=True)
    price = fields.Float('Tổng tiền')
    description = fields.Char('Ghi chú')




class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    contract_id = fields.Many2one('apartment.contract')

