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

		var field;

		switch (this._type) {
			case 'string':
			case 'integer':
			case 'password':
			case 'list':
				if (this.choices)
					field = new boto_web.ui.dropdown(props);
				else if (props.maxlength > 1024)
					field = new boto_web.ui.textarea(props);
				else
					field = new boto_web.ui.text(props);
				break;
			case 'dateTime':
				field = new boto_web.ui.date(props);
				break;
			case 'blob':
				field = new boto_web.ui.file(props);
				break;
			case 'object':
				field = new boto_web.ui.picklist(props);
				break;
		}

		if (typeof field == 'undefined') return;

		field.node.appendTo(self.node)
	});
};
