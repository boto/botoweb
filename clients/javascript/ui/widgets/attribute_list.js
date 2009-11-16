/**
 * @author    Ian Paterson
 * @namespace boto_web.ui.widgets.editing_tools
 */

/**
 * Displays object editing links based on the actions available to the user.
 *
 * @param node where to insert the icons.
 */
boto_web.ui.widgets.AttributeList = function(node, model, obj) {
	var self = this;

	self.node = $(node).addClass('widget-attribute_list');
	self.model = model;

	$(self.model.properties).each(function() {
		var props = this;

		if (typeof obj != 'undefined')
			props = $.extend(this, {value: obj.properties[this.name]});

		if (props._perm && $.inArray('read', props._perm) == -1)
			return;

		var field = boto_web.ui.forms.property_field(props, {read_only: true});

		if (typeof field == 'undefined') return;

		field.node.appendTo(self.node)
	});
};
