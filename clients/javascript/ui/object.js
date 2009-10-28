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

	self.get_link = function(method) {
		var base_url = document.location.href + '';
		base_url = base_url.replace(/action=.*?(&|$)/,'');
		if (base_url.indexOf('?') == -1)
			base_url += '?';
		else
			base_url += '&';

		switch (method) {
			case 'get':
				return '#' + boto_web.env.opts.model_template.replace('*', self.model.name) + '?id=' + self.obj.id;
				break;
			case 'put':
				return base_url + 'action=edit/' + self.model.name + '/' + self.obj.id;
				break;
			case 'delete':
				return base_url + 'action=delete/' + self.model.name + '/' + self.obj.id;
				break;
		}
	};

	/**
	 * Insert values from the object into the html markup.
	 */
	self.parse_markup = function() {
		var nested_obj_nodes = [];

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

			var template = $(this).contents().clone();
			$(this).empty();

			var node = $(this).clone();
			nested_obj_nodes.push([this, node]);

			for (var i in relations) {
				self.obj.follow(relations[i].name, function(data) {
					$(data).each(function() {
						node.append(new boto_web.ui.Object(template, boto_web.env.models[this.name], this).node)
					});
					new boto_web.ui.widgets.DataTable(node.parent('table'))
				});
			}

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

		// Insert object attributes
		var sel = boto_web.ui.selectors.attribute;
		var prop = boto_web.ui.properties.attribute;

		self.node.find(sel).each(function() {
			var val = $(this).attr(prop);

			if (val in self.model.properties)
				alert($.dump(self.model.properties[val].perms));

			// Decide whether this is a valid property.
			if (!(val in self.obj.properties) || (val in self.model.properties && $.inArray('read', self.model.properties[val].perms == -1))) {
				$(val).log(self.model.name + ' does not support this property');
				return;
			}

			if (this.tagName.toLowerCase() == 'img')
				$(this).attr('src', self.obj.properties[val]);
			else
				$(this).text(self.obj.properties[val].toString());
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

		$(nested_obj_nodes).each(function() {
			$(this[0]).replaceWith(this[1]);
			$(this[1]).trigger('ready');
		});
	};

	self.parse_markup();
};
