odoo.define('hr_applicant_tracking.clipboard', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;

    publicWidget.registry.ClipboardButton = publicWidget.Widget.extend({
        selector: '.o_clipboard_button',
        events: {
            'click': '_onClick',
        },

        /**
         * @override
         */
        start: function () {
            this._super.apply(this, arguments);
            if (!navigator.clipboard) {
                this.$el.hide();
            }
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         * @param {Event} ev
         */
        _onClick: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            
            var $target = $(ev.currentTarget);
            var text = $target.data('clipboard-text') || '';
            
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(function() {
                    var $copied = $('<span>', {
                        class: 'text-success ml-2',
                        text: _t('Copied!')
                    });
                    $target.after($copied);
                    setTimeout(function() {
                        $copied.fadeOut(400, function() {
                            $(this).remove();
                        });
                    }, 2000);
                }).catch(function(err) {
                    console.error('Could not copy text: ', err);
                });
            }
        },
    });
});
