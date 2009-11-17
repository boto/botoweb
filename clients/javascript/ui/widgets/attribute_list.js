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

	self.node = $(node).addClass('widget-attribute_list clear');
	self.template = $('<div/>').append(self.node.contents().clone());
	self.node.empty();
	self.model = model;
	self.properties = [];
	self.sequence = self.node.attr(boto_web.ui.properties.attributes);

	if (self.sequence && self.sequence != 'all')
		self.sequence = self.sequence.split(',')
	else
		self.sequence = self.model.properties.splice();

	self.properties = $.map(self.sequence, function(name, num) {
		if (!(name in self.model.prop_map))
			return;

		var props = self.model.prop_map[name];

		if (props._perm && $.inArray('read', props._perm) == -1)
			return;

		//if (!obj.properties[props.name])
		//	return;

		return props;
	});

	/*if (self.properties.length > 20) {
		self.per_column = Math.ceil(self.properties.length / 3);
		self.columns = [
			$('<div/>')
				.addClass('al p33')
				.appendTo(self.node),
			$('<div/>')
				.addClass('al p33')
				.appendTo(self.node),
			$('<div/>')
				.addClass('al p33')
				.appendTo(self.node)
		]
	}
	else if (self.properties.length > 5) {*/
		self.per_column = Math.ceil(self.properties.length / 2);
		self.columns = [
			$('<div/>')
				.addClass('al p50')
				.appendTo(self.node),
			$('<div/>')
				.addClass('al p50')
				.appendTo(self.node)
		]
	/*}
	else {
		self.per_column = 1e99;
		self.columns = [
			$('<div/>')
				.appendTo(self.node)
		]
	}*/

	$(self.properties).each(function(num, props) {
		var c = self.columns[Math.floor(num / self.per_column)];

		var template = self.template.find(boto_web.ui.selectors.attribute.replace(']', '=' + props.name + ']'));

		var container = $('<div/>')
			.addClass('property');

		if (template.length)
			container.append(template);
		else
			container.attr(boto_web.ui.properties.attribute, props.name);

		c.append(
			$('<label/>')
				.addClass('property_label')
				.text(props._label),
			container,
			$('<br class="clear"/>')
		);
	});
};
