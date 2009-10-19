/**
 * @author    Ian Paterson
 * @namespace boto_web.ui.object
 */

/**
 * Encapsulates content related to a particular object and provides access to
 * that object's properties.
 *
 * @param html an HTML document fragment for parsing.
 */
boto_web.ui.Object = function(html, model, obj, action) {
	var self = this;

	self.model = model;
	self.obj = obj;
	self.node = $(html);
	self.guid = self.model.name + '_' + self.obj.id;

	/*
	if (action == 'edit') {
		var store = $.jStore.get('recent_edited'));
		if ($.inArray(self.guid, store)) {
			store.remove(self.guid);
		}
		else

	}
	else {
		var store = $.jStore.get('recent_viewed'));
	}
	*/

	self.get_link = function(method) {
		switch (method) {
			case 'get':
				return '#' + boto_web.env.opts.model_template.replace('*', self.model.name) + '?' + self.obj.id;
				break;
			case 'put':
				return '#' + boto_web.env.opts.model_template.replace('*', self.model.name) + '?' + self.obj.id + '&edit';
				break;
			case 'delete':
				return '#' + boto_web.env.opts.model_template.replace('*', self.model.name) + '?' + self.obj.id + '&delete';
				break;
		}
	};

	/**
	 * Insert values from the object into the html markup.
	 */
	self.parse_markup = function() {
		// Insert object attributes
		var sel = boto_web.ui.selectors.attribute;
		var prop = boto_web.ui.properties.attribute;

		self.node.find(sel).each(function() {
			var val = $(this).attr(prop);

			// Decide whether this is a valid property.
			if (!(val in self.obj.properties)) {
				$(val).log(self.model.name + ' does not support this property');
				return;
			}

			if (this.tagName.toLowerCase() == 'img')
				$(this).attr('src', self.obj.properties[val]);
			else
				$(this).text(self.obj.properties[val]);
		});

		// Add editing tools
		sel = boto_web.ui.selectors.editing_tools;

		self.node.find(sel).each(function() {
			new boto_web.ui.widgets.EditingTools(this, self.model);
		});


		// Add links
		sel = boto_web.ui.selectors.link;
		prop =  boto_web.ui.properties.link;

		self.node.find(sel).each(function() {
			// Translate
			var val = $(this).attr(prop);
			var method = {'view':'get', 'edit':'put', 'delete':'delete'}[val];

			// Only allow view, edit, or delete and only if that action is allowed
			// according to the model API.
			if (!(method && method in self.model.methods)) {
				$(val).log(self.model.name + ' does not support this action');
				return;
			}

			$(this).attr('href', self.get_link(method));
		});


		// Add relational links to other objects
		sel = boto_web.ui.selectors.relations;

		self.node.find(sel).each(function() {
			var props = $(this).attr(boto_web.ui.properties.attributes) || 'all';

			if (props != 'all')
				props = props.split(',');

			var relations = [];

			// Find any relations matching the props list
			for (var prop in self.obj.properties) {
				if (self.obj.properties[prop].type == 'reference' && (props == 'all' || $.inArray(prop, props) >= 0)) {
					relations.push(self.obj.properties[prop]);
				}
			}

			var node = $('<div/>')
				.appendTo(this);
			$('<br/>')
				.addClass('clear')
				.appendTo(this);

			for (var i in relations) {
				$('<a/>')
					.text(relations[i].name)
					.appendTo($('<h3/>').appendTo(node));
				$('<div/>')
					.text('Related objects will be listed here.')
					.appendTo(node);
			}

			node.accordion({});

			// If no relations are found, return an error
			if (props.length == 0) {
				$($(this).attr(prop)).log(self.model.name + ' no valid relations found');
				return;
			}
		});

		// Add attribute lists
		sel = boto_web.ui.selectors.attribute_list;

		self.node.find(sel).each(function() {
			new boto_web.ui.widgets.AttributeList(this, self.model, self.obj);
		});

		// Toggle details
		sel = boto_web.ui.selectors.details;

		self.node.find(sel).each(function() {
			$(this).find('legend').click(function() {
				$(this.parentNode).find('.widget-attribute_list').toggle();
			});
		});
	};

	self.do_action = function(action) {
		if (action == 'edit')
			self.obj.edit();
		else if (action == 'delete')
			self.obj.del();
	};

	self.parse_markup();
	self.do_action(action);
};
