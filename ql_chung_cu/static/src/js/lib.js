// MOi 100%

openerp.web.form.FieldPhone = openerp.web.form.FieldChar.extend({
    template: 'FieldUrl',
    initialize_content: function() {
        this._super();
        var $button = this.$el.find('button');
        $button.click(this.on_button_clicked);
        this.setupFocus($button);
    },
    render_value: function() {
        if (!this.get("effective_readonly")) {
            this._super();
        } else {
            var tmp = this.get('value');
            var s = /(\w+):(.+)|^\.{0,2}\//.exec(tmp);
            if (!s) {
                tmp = "tell:" + this.get('value');
            }
            var text = this.get('value') ? this.node.attrs.text || tmp : '';
            this.$el.find('a').attr('href', tmp).text(text);
        }
    },
    on_button_clicked: function() {
        if (!this.get('value')) {
            this.do_warn(_t("Resource Error"), _t("This resource is empty"));
        } else {
            var url = $.trim(this.get('value'));
            if(/^www\./i.test(url))
                url = url;
            window.open(url);
        }
    }
});

openerp.web.form.widgets = new instance.web.Registry({
    'phone' : 'instance.web.form.FieldPhone',
});
//end moi