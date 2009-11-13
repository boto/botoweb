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

	self.get_link = function(method, data) {
		var base_url = document.location.href + '';
		base_url = base_url.replace(/action=.*?(&|$)/,'');
		if (base_url.indexOf('?') == -1)
			base_url += '?';
		else
			base_url += '&';

		switch (method) {
			case 'view':
				if (data)
					return boto_web.env.base_url + self.model.href + '/' + self.obj.id + '/' + escape(data);

				return '#' + boto_web.env.opts.model_template.replace('*', self.model.name) + '?id=' + self.obj.id;
			// TODO phase out update(properties) in favor of edit(properties)
			case 'update':
			case 'edit':
				if (data)
					return base_url + 'action=update/' + self.model.name + '/' + self.obj.id + '&data=' + escape(data);

				return base_url + 'action=edit/' + self.model.name + '/' + self.obj.id;
			case 'delete':
				return base_url + 'action=delete/' + self.model.name + '/' + self.obj.id;
		}
	};

	/**
	 * Insert values from the object into the html markup.
	 */
	self.parse_markup = function() {
		var nested_obj_nodes = [];

		// Check conditional functions which might drop sections from the DOM
		sel = boto_web.ui.selectors.condition;
		prop =  boto_web.ui.properties.condition;

		self.node.find(sel).each(function() {
			var val = $(this).attr(prop);
			if (val in boto_web.env.opts.conditions)
				boto_web.env.opts.conditions[val](self.obj, this, self);
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

			var template = $(this).contents().clone();
			$(this).empty();

			var node = $(this).clone();
			nested_obj_nodes.push([this, node]);

			for (var i in relations) {
				self.obj.follow(relations[i].name, function(data) {
					$(data).each(function() {
						node.append(new boto_web.ui.Object(template.clone(), boto_web.env.models[this.name], this).node)
					});
					new boto_web.ui.widgets.DataTable(node.parent('table'));
				});
			}

			// If no relations are found, return an error
			if (props.length == 0) {
				$($(this).attr(prop)).log(self.model.name + ' no valid relations found');
				return;
			}
		});

		// Insert object attributes
		var sel = boto_web.ui.selectors.attribute;
		var prop = boto_web.ui.properties.attribute;

		for (var i in [0,1]) {
			self.node.find(sel).each(function() {
				var val = $(this).attr(prop).split('.');
				var follow_props;

				// Allow a.b.c reference attribute following
				if (val.length > 1) {
					follow_props = val.splice(1);
					val = val[0];
				}
				else
					val = val[0];

				// Decide whether this is a valid property.
				if (val in self.model.properties && self.model.properties[val]._perm && $.inArray('read', self.model.properties[val]._perm) == -1) {
					$(val).log(self.model.name + ' does not support this property');
					$(this).empty();
					return;
				}
				else if (!(val in self.obj.properties)) {
					$(this).empty();
					return;
				}

				if (this.tagName.toLowerCase() == 'img')
					$(this).attr('src', self.obj.properties[val]);
				// Load nested objects
				else if ((self.obj.properties[val].type in {reference:1,query:1} || self.model.prop_map[val] && self.model.prop_map[val]._type == 'list')) {
					var container;

					// Find the best container to hold the new content, if the tag with
					// this attribute is the only child in its parent object then we
					// can use the natural parent, otherwise we generate a new span.
					if ($(this).siblings().length == 0 && $(this).parent()) {
						container = $(this).parent().clone();
						nested_obj_nodes.push([$(this).parent(), container]);
						$(this).parent().empty();
					}
					else {
						container = $('<span/>');
						nested_obj_nodes.push([this, container]);
					}

					var node = $(this).clone();

					$(this).empty();
					container.empty();

					if (!follow_props && !node.html())
						follow_props = ['name'];
					if (follow_props)
						node.attr(boto_web.ui.properties.attribute, follow_props.join('.'));
					else
						node.attr(boto_web.ui.properties.attribute, '');

					// Follow references if this is a reference or query type
					if (self.model.prop_map[val]._item_type in boto_web.env.models) {
						self.obj.follow(val, function(objs) {
							$(objs).each(function() {
								var n = $('<span/>').append(node.clone()).appendTo(container);
								new boto_web.ui.Object(n, boto_web.env.models[this.properties.model], this);
							});
						});
					}
					// For string lists, duplicate the node for each value
					else if (self.model.prop_map[val] && self.model.prop_map[val]._type == 'list') {
						var values = self.obj.properties[val];
						if (!$.isArray(values))
							values = [values];
						$(values).each(function() {
							node.clone()
								.html(this.toString())
								.appendTo(container);
						});
					}
				}
				else if (prop == boto_web.ui.properties.class_name) {
					$(this).addClass('model-' + self.obj.properties.model);
					$(this).addClass('value-' + self.obj.properties[val].toString().replace(/\s[\s\S]*$/, ''));
				}
				else
					$(this).text(self.obj.properties[val].toString());
			});

			// Insert object attributes as classNames
			var sel = boto_web.ui.selectors.class_name;
			var prop = boto_web.ui.properties.class_name;
		}

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

		// Insert datetimes
		sel = boto_web.ui.selectors.date_time;

		self.node.find(sel).each(function() {
			new boto_web.ui.widgets.DateTime(this);
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
			var data;
			if (/(.*)\((.*)\)/.test(val)) {
				val = RegExp.$1;
				data = RegExp.$2;
			}

			var model = self.model;

			if (val == 'create') {
				if ($(this).is(boto_web.ui.selectors.model))
					model = $(this).attr(boto_web.ui.properties.model);
				else
					model = $(this).parents(boto_web.ui.selectors.model + ':eq(0)').attr(boto_web.ui.properties.model);

				model = boto_web.env.models[model] || '';
			}

			var method = {'create':'post', 'view':'get', 'update':'put', 'edit':'put', 'delete':'delete'}[val];

			// Only allow view, edit, or delete and only if that action is allowed
			// according to the model API.
			if (!(method && method in model.methods)) {
				$(val).log(model.name + ' does not support this action');
				return;
			}

			// Get defaults for the create form.
			if (val == 'create' && data) {
				// Convert barewords to object property values
				while (/:\s*([a-z_]\w*)\s*(,|\})/i.test(data)) {
					data = data.replace(/:\s*([a-z_]\w*)\s*(,|\})/i, function(a,b,c) {
						return ': "' + self.obj.properties[b] + '"' + c;
					})
				}

				eval('data = ' + data);

				$(this).click(function(e) {
					model.create({def: data});
					e.preventDefault();
				})
			}

			$(this).attr('href', self.get_link(val, data));
		});

		$(nested_obj_nodes).each(function() {
			$(this[0]).replaceWith(this[1]);
			$(this[1]).trigger('ready');
		});
	};

	self.parse_markup();
};
