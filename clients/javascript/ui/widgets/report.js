/**
 * @author    Ian Paterson
 * @namespace boto_web.ui.widgets.report
 */

/**
 * Allows the user to generate a report.
 *
 * @param node the node containing the report template.
 */
boto_web.ui.widgets.Report = function(node) {
	var self = this;

	self.node = $(node);
	self.breadcrumbs = self.node.parent().find("ul.breadcrumbs");
	self.model = null;
	self.obj = {};
	self.filters = [];
	self.columns = [];
	self.has_columns = false;

	self.step_1 = function() {
		if (!self.template) {
			self.template = $(self.node).clone(true);
		}
		self.node.find('article:not(#step_1)').remove();
		self.node.find('#step_1').show();
		self.node.parent().find('#next_step').hide();
		self.filters = [];
		self.columns = [];

		// Add the breadcrumbs
		self.breadcrumbs.html('<li>Reporting</li>');

		var models = [];

		for (var name in boto_web.env.models)
			models.push(name);

		models = models.sort(boto_web.ui.sort_props);

		$.map(models, function(name) {
			$('<div/>')
				.addClass('ui-button ui-state-default ui-corner-all')
				.html('<strong>' + name + '</strong>')
				.click(function(name){ return function() {
					self.model = boto_web.env.models[name];
					document.title = name + ' Report';
					$('h1').text(document.title);
					document.location.href = self.get_link(2);
				}}(name))
				.appendTo(self.node.find('.new_report'))
				.each(function() {
					var seen = {};
					var links = $.map(boto_web.env.models[name].properties, function(p){
						if ((p._type == 'reference' || p._type == 'query') && !seen[p._item_type]) {
							seen[p._item_type] = 1;
							return p._item_type;
						}
						return null;
					}).join(', ');

					if (links) {
						$('<span/>')
							.text('Links to ' + links)
							.appendTo(this);
					}
				})
				.append($('<br class="clear"/>'));
		});
		boto_web.ui.decorate(self.node);
	}

	self.step_2 = function(e) {
		if (!self.template) {
			self.template = $(self.node).clone(true);
		}
		self.node.find('article:not(#step_1)').remove();
		self.node.find('#step_1').hide();
		self.template.find('#step_2').clone(true).appendTo(self.node);

		self.has_columns = self.has_columns || self.columns.length > 0;

		// Add the breadcrumbs
		self.breadcrumbs.empty();
		self.add_breadcrumb(1, "Reporting");
		self.breadcrumbs.append('<li>' + self.model.name + ' Filters</li>');

		self.build_attribute_choices(function(e, p) {
			self.add_filter(e, p);
		});

		self.node.find("#preview_button").remove();
		$('<div/>')
			.attr("id", "preview_button")
			.addClass('ui-button ui-state-default ui-corner-all')
			.html('<span class="ui-icon ui-icon-refresh"></span>Refresh result preview')
			.click(function() {
				self.filters = self.get_filters();
				self.node.find('#step_2 .preview').empty();
				self.build_results(true, self.node.find("#step_2 .preview"));
			})
			.insertBefore(self.node.find('.preview'));

		self.node.find(".preview").empty();
		$('<br/>')
			.addClass('clear')
			.appendTo(self.node.find('.preview'));

		self.node.parent().find('#next_step')
			.show()
			.unbind()
			.click(function() {
				self.filters = self.get_filters();

				if (!self.has_columns)
					self.columns = [];

				document.location.href = self.get_link(3);
			})
			.find('em').html('<strong>Modify the report</strong> by choosing the appropriate columns.');

		boto_web.ui.decorate(self.node);

		if (self.filters.length) {
			$(self.filters).each(function() {
				if (this[0] in self.model.prop_map)
					self.add_filter(null, self.model.prop_map[this[0]], this[1], this[2]);
			});
		}
	}

	self.step_3 = function() {
		if (!self.template) {
			self.template = $(self.node).clone(true);
		}
		self.node.find('article:not(#step_1)').remove();
		self.node.find('#step_1').hide();
		self.template.find('#step_3').clone(true).appendTo(self.node);

		self.has_columns = true;

		// Add the breadcrumbs
		self.breadcrumbs.empty();
		self.add_breadcrumb(1, "Reporting");
		self.add_breadcrumb(2, self.model.name + ' Filters');
		self.breadcrumbs.append('<li>Columns</li>');

		self.node.find('#column_editor_container').hide();

		var set_sort_icons = function() {
			if (self.node.find('.column_list li').length > 1) {
				self.node.find('.column_list li span:first-child').attr('className', 'ui-icon ui-icon-arrowthick-2-n-s');
				self.node.find('.column_list li:first > span:first').attr('className', 'ui-icon ui-icon-arrowthick-1-s');
				self.node.find('.column_list li:last > span:first').attr('className', 'ui-icon ui-icon-arrowthick-1-n');
			}
			else {
				self.node.find('.column_list li > span:first').attr('className', 'ui-icon ui-icon-bullet');
			}
		};

		self.build_attribute_choices(function(e, p) {
			var li = $('<li/>')
				.addClass('ui-state-default')
				.attr('id', 'column_' + p.name)
				.append(
					$('<span></span>'),
					$('<span class="ui-icon ui-icon-closethick clickable"/>')
						.attr('title', 'Remove column')
						.click(function() { $(this).parent().remove() }),
					$('<span/>')
						.addClass('ui-icon ui-icon-pencil clickable')
						.attr('title', 'Edit column')
						.click(function() {
							self.edit_column(self.model, p.name, null, $(this).parent().find('.column_editor'));
						}),
					$('<span/>')
						.addClass('ui-icon ui-icon-copy clickable')
						.attr('title', 'Clone column')
						.click(function() {
							var new_column = $(this).parent('li').clone(true).insertAfter($(this).parent('li'));
							self.edit_column(self.model, p.name, null, new_column.find('.column_editor'));
						}),
					$('<label/>')
						.html(p._label),
					$('<div class="hidden column_editor"/>')
				)
				.appendTo(self.node.find('.column_list ul'));

			// Used to preload column data when an existing report is edited
			if ($(e.target).data('default_column')) {
				var data = $(e.target).data('default_column');
				li.find('.column_editor').data('column_data', data);
				$(e.target).data('default_column', '')

				if (data[0] != p._label)
					li.find('label').html(data[0] + ' <small>(was: ' + p._label + ')</small>');
			}
			else {
				li.find('.column_editor').data('column_data', [p._label, p.name]);
			}

			set_sort_icons();

			self.edit_column(self.model, '');
		});


		$('<ul/>')
			.sortable({
				stop: function() {
					set_sort_icons();
				}
			})
			.disableSelection()
			.appendTo(self.node.find('.column_list'));

		self.node.find("#preview_button").remove();
		$('<div/>')
			.attr("id", "preview_button")
			.addClass('ui-button ui-state-default ui-corner-all')
			.html('<span class="ui-icon ui-icon-refresh"></span>Refresh result preview with selected columns')
			.click(function() {
				self.columns = self.get_columns();
				self.node.find('#step_3 .preview').empty();
				self.build_results(true, self.node.find("#step_3 .preview"));
			})
			.insertBefore(self.node.find('.preview'));

		self.node.find(".preview").empty();
		$('<br/>')
			.addClass('clear')
			.appendTo(self.node.find('.preview'));


		self.node.parent().find('#next_step')
			.show()
			.unbind()
			.click(function() {
				self.columns = self.get_columns();
				document.location.href = self.get_link(4);
			})
			.find('em').html('<strong>Generate the report</strong> and export the results.');

		if (self.columns) {
			$(self.columns).each(function() {
				if ($.isArray(this[1]))
					self.node.find('#' + this[1][0] + '.attribute').data('default_column', this).click();
				else
					self.node.find('#' + this[1] + '.attribute').data('default_column', this).click();
			});
		}
	}

	self.step_4 = function() {
		if (!self.template) {
			self.template = $(self.node).clone(true);
		}
		self.node.find('article:not(#step_1)').remove();
		self.node.find('#step_1').hide();
		self.node.parent().find('#next_step').hide();
		self.template.find('#step_4').clone(true).appendTo(self.node);

		// Add the breadcrumbs
		self.breadcrumbs.empty();
		self.add_breadcrumb(1, "Reporting");
		self.add_breadcrumb(2, self.model.name + ' Filters');
		self.add_breadcrumb(3, "Columns");
		self.breadcrumbs.append('<li>Results</li>');

		$('#next_step').hide();

		self.node.find("#step_4 .results").empty();

		self.query = 'model=' + self.model.name
			+ '&filters=' + escape($.toJSON(self.filters))
			+ '&columns=' + escape($.toJSON(self.columns));

		$("<br/>").addClass("clear").appendTo(self.node.find("#step_4 .results"));

		if (self.obj.id) {
			$('<div/>')
				.addClass('ui-button ui-state-default ui-corner-all')
				.html('<span class="ui-icon ui-icon-disk"></span>Update Report')
				.click(function() {
					self.obj.properties.target_class_name = escape(self.model.name);
					self.obj.properties.filters = escape($.toJSON(self.filters));
					self.obj.properties.query = escape($.toJSON(self.columns));
					self.obj.edit({hide: ['query','target_class_name','filters','input_params']});
				})
				.appendTo(self.node.find('#step_4 .results'));
		}

		$('<div/>')
			.addClass('ui-button ui-state-default ui-corner-all')
			.html('<span class="ui-icon ui-icon-document"></span>Save as New Report')
			.click(function() {
				// Ensure that fields are blank.
				$.each(boto_web.env.models.Report.properties, function() {
					delete this.value;
				});
				boto_web.env.models.Report.create({def: {
					target_class_name: escape(self.model.name),
					filters: escape($.toJSON(self.filters)),
					query: escape($.toJSON(self.columns))
				}, hide: ['query','target_class_name','filters','input_params']});
			})
			.appendTo(self.node.find('#step_4 .results'));

		self.build_results(false, self.node.find("#step_4 .results"));

		setTimeout(function() {
			if (self.obj.id) {
				$("<div/>")
					.addClass('smaller jr')
					.html("<strong>Link to this report:</strong> " + self.get_link('report') + '?id=' + self.obj.id)
					.appendTo(self.node.find("#step_4 .results"));
			}
		}, 1000);
	}

	self.build_results = function(preview, resultNode){
		var thead = $('<thead/>');
		var tbody = $('<tbody/>');
		var trhead = $('<tr/>').appendTo(thead);
		var trbody = $('<tr/>')
			.addClass('bwObject')
			.appendTo(tbody);

		$.map(self.columns, function(c) {
			var p;
			if ($.isArray(c)) {
				if ($.isArray(c[1])) {
					p = {_label: c[0], name: c[1][0]};
				}
				else {
					p = {_label: c[0], name: c[1]};
				}
			}
			else {
				p = {_label: self.model.prop_map[c]._label, name: c};
			}

			$('<th/>')
				.text(p._label || '')
				.appendTo(trhead);

			var is_list = p.name in self.model.prop_map && self.model.prop_map[p.name]._type == 'list';
			var is_ref = p.name in self.model.prop_map && self.model.prop_map[p.name]._item_type in boto_web.env.models;
			var linked_name = $('<a/>')
				.attr(boto_web.ui.properties.attribute, 'name')
				.attr(boto_web.ui.properties.link, 'view');
			var node = $('<span/>')
				.attr(boto_web.ui.properties.attribute, p.name);
			var list_node;


			if (p.name == 'name') {
				$('<td/>')
					.append(linked_name)
					.appendTo(trbody);
			}
			else if (is_ref) {
				if ($.isArray(c[1])) {
					var nested_markup = function(prop, nested) {
						var n = $((is_list && !nested) ? '<li/>' : '<span/>')
							.attr(boto_web.ui.properties.attribute, prop[0])

						if (is_list && nested)
							is_list = false;

						if (prop.length == 3)
							n.attr(boto_web.ui.properties.filter, $.toJSON(prop[2]));

						if ($.isArray(prop[1]))
							n.append(nested_markup(prop[1], true));
						else if (prop.length > 1)
							n.append(nested_markup([prop[1] || 'name'], true))

						if (n.is('li'))
							n = $('<ul/>').append(n);

						return n
					};

					$('<td/>')
						.append(nested_markup(c[1]))
						.appendTo(trbody);
				}
				else {
					$('<td/>')
						.append(node.append(linked_name))
						.appendTo(trbody);
				}
			}
			else if (is_list) {
				list_node = $('<li/>')
					.attr(boto_web.ui.properties.attribute, p.name)
					.append(is_ref ? linked_name : null)

				$('<td/>')
					.append($('<ul/>').append(list_node))
					.appendTo(trbody);
			}
			else {
				$('<td/>')
					.append(node)
					.appendTo(trbody);
			}
		});

		$('<table/>')
			.append(thead)
			.append(tbody)
			.appendTo(resultNode);

		self.results = new boto_web.ui.widgets.SearchResults(tbody, self.model, {min_memory: !preview});

		self.model.query(self.filters, function(data, page, count) {
			return self.results.update(data, page, count) && !preview;
		});

	}

	self.update = function() {
		if (self.results) {
			self.results.stop();
		}
		if (/model=(.*?)(?:&filters=(.*?)(?:&columns=(.*?)(?:&id=(.*?))?)?)?(&|$)/.test(document.location.href)) {
			self.query = RegExp.lastMatch;
			self.model = boto_web.env.models[RegExp.$1];

			if (RegExp.$2)
				self.filters = $.evalJSON(unescape(RegExp.$2));
			if (RegExp.$3) {
				self.columns = $.evalJSON(unescape(RegExp.$3));
			}
			if (RegExp.$4 && !self.obj.id) {
				self.obj = {id: RegExp.$4, properties: {}};
				boto_web.env.models.Report.get(RegExp.$4, function(obj) {
					self.obj = obj;
				});
			}
		}
		else {
			self.step_1();
			return;
		}

		if (/step=(\d+)/.test(document.location.href)) {
			self['step_' + RegExp.$1]();
		}
		else if (self.model && self.filters && self.columns) {
			self.step_4();
		}
		else {
			self.step_1();
		}
	}

	self.build_attribute_finder = function(base_node) {
		if (!base_node)
			base_node = self.node;

		var blur_text = 'Find an attribute';
		return $('<input/>')
			.val(blur_text)
			.css('color', '#999')
			.focus(function() {
				if (this.value == blur_text) {
					$(this)
						.val('')
						.css('color', '');
				}
			})
			.blur(function() {
				if (!this.value) {
					$(this)
						.val(blur_text)
						.css('color', '#999');
				}
			})
			.keyup(function(e) {
				var input = this;

				if (e.keyCode == 13) {
					base_node.find('.attributes .attribute:visible:first').click();
					$(input).val('').keyup();
				}
				else if (input.value) {
					base_node.find('.attribute').each(function() {
						var attr = $(this).find('.attribute_value');

						if (!attr.length)
							attr = $(this);

						if (attr.text().toLowerCase().indexOf(input.value.toLowerCase()) >= 0)
							$(this).show();
						else
							$(this).hide();
					});
				}
				else {
					base_node.find('.attribute').show();
				}
			});
	}

	self.build_attribute_choices = function(click_fcn, model, base_node) {
		if (!base_node)
			base_node = self.node;

		if (!model)
			model = self.model;

		if (model.properties.length > 10) {
			self.narrow_filters = self.build_attribute_finder(base_node)
				.insertBefore(base_node.find('.attributes'));
			$('<br/>').insertBefore(base_node.find('.attributes'));
		}

		// Add ID to the property list... pushing the properties array does not work
		var props = [{_label: 'ID', name: 'id', _perm: ['read'], _type: 'string'}];
		$(model.properties).each(function() { props.push(this); });
		props.sort(boto_web.ui.sort_props)

		$.map(props, function(p) {
			if ($.inArray('read', p._perm) < 0)
				return;

			$('<div/>')
				.addClass('attribute attribute_value ui-button ui-state-default ui-corner-all')
				.attr('id', p.name)
				.html(p._label)
				.click(function(e) { return click_fcn(e, p); })
				.appendTo(base_node.find('.attributes'));
		});
	}

	self.get_filters = function(base_node) {
		if (!base_node)
			base_node = self.node;

		var filter_columns = {name: 1};
		var filters = [];

		// Take only the first set of filters, others may be nested
		base_node.find('.filters:first .filter').each(function() {
			var prop = $(this).find('.property').attr('id').replace('property_', '');
			var op = $(this).find('.operator').val();
			val = $(this).find('.field_container').data('get_value')();

			if (!$.isArray(val))
				val = [val];

			op = {'is': '=', 'is not': '!=', 'contains': 'like'}[op] || op;

			if (op == 'like')
				val = $.map(val, function(v) { return v ? '%' + v + '%' : null; });
			if (op == 'starts with') {
				val = $.map(val, function(v) { return v ? v + '%' : null; });
				op = 'like';
			}
			if (op == 'ends with') {
				val = $.map(val, function(v) { return v ? '%' + v : null; });
				op = 'like';
			}

			if (val.length == 1)
				val = val[0];

			if (!filter_columns[prop])
				filter_columns[prop] = 1;

			filters.push([prop, op, val]);
		});

		if (!self.has_columns) {
			self.columns = [];
			for (var prop in filter_columns) {
				var c = self.model.prop_map[prop];
				self.columns.push([c._label, c.name]);
			}
		}

		return filters;
	}

	self.add_filter = function(e, property, operator, value, base_node) {
		if (!base_node)
			base_node = self.node

		if (operator == 'like') {
			var val = value;
			if ($.isArray(val))
				val = val[0];

			if (/^%.*%$/.test(value))
				operator = 'contains'
			else if (/^%/.test(value))
				operator = 'ends with'
			else if (/%$/.test(value))
				operator = 'starts with'

			if ($.isArray(value)) {
				value = $.map(value, function(v) {
					return v.replace(/^%|%$/g,'');
				});
			}
			else
				value = value.replace(/^%|%$/g,'');
		}
		else if (operator == '=')
			operator = 'is';
		else if (operator == '!=')
			operator = 'is not';

		// Avoid the phantom field value bug
		property.value = null;

		// Create a field which allows multiple selections regardless of the item type
		var field = boto_web.ui.forms.property_field(property, {
			allow_multiple: true,
			allow_default: true,
			read_only: false,
			_default_value: value || ''
		});

		$('<div/>')
			.addClass('filter editor ui-button ui-state-default ui-corner-all')
			.appendTo(base_node.find('.filters:first'))
			.append(
				$('<select/>')
					.addClass('operator ar')
					.each(function() {
						var select = this;
						var operators = ['contains', 'starts with', 'ends with', 'is', 'is not', '>', '<', '>=', '<='];
						if (property._type == 'reference')
							operators = ['is', 'is not'];
						if (property._type == 'boolean')
							operators = ['is'];
						if (property._type == 'dateTime')
							operators = ['is', 'is not', '>', '<', '>=', '<='];
						$(operators).each(function() {
							$('<option/>').attr({text: this, value: this}).appendTo(select);
						})
					}).val(operator || ''),
				$('<h3/>')
					.addClass('property')
					.attr('id', 'property_' + property.name)
					.text(property._label)
					.prepend($('<span/>')
						.addClass('ui-icon ui-icon-closethick')
						.click(function() {
							$(this).parents('.filter').remove()
						})
					),
				$('<br class="clear" />'),
				field.field_container,
				field.button_add
			)
			.find('.field_container br.clear, .field_container .ui-button').remove();

		field.field_container.find('input, select, textarea').focus();

		if (e)
			e.preventDefault();
	}

	self.get_columns = function(base_node, single_column) {
		if (!base_node)
			base_node = self.node.find('.column_list ul li');

		// Finalize any changes made in the column editor
		if (!single_column)
			self.edit_column(self.model, '');

		var columns = [];
		base_node.each(function() {
			if ($(this).find('.column_editor').data('column_data')) {
				columns.push($(this).find('.column_editor').data('column_data'));
				return true;
			}

			var query = [];

			// Start with the column name
			query.push($(this).find('.rename_column').val());

			// Reference properties may be nested to change what is displayed
			if ($(this).find('.display .display .display').length) {
				var expand_query = function(prop, parent) {
					var q = [prop];
					var sub_prop = parent.find('.sub_prop:first').val() || ''
					var expanded = false;

					parent = parent.find('.display:first');

					if (parent.find('.display').length) {
						q.push(expand_query(sub_prop, parent));
						expanded = true;
					}
					else {
						q.push(sub_prop);
					}

					// TODO push filtering details
					var filter_parent = parent.parent('.display');
					filter_parent.find('.display').remove();
					var filters = self.get_filters(filter_parent);

					if (filters.length) {
						/*if (!expanded) {
							q[1] = [q[1], ''];
						}*/
						q.push(filters);
					}

					return q;
				};

				query.push(expand_query($(this).find('.prop_name:first').attr('title'), $(this).find('.display:first')));
			}
			else {
				query.push($(this).find('.prop_name:first').attr('title'));

				var sub_prop = $(this).find('.sub_prop:first').val() || '';

				var filters = self.get_filters(base_node);

				if (filters.length) {
					query[1] = [query[1], sub_prop, filters];
				}
				else if (sub_prop) {
					query[1] = [query[1], sub_prop];
				}
			}

			columns.push(query);
		});

		return columns;
	}

	self.edit_column = function(model, prop, parent, column_node) {
		// id is not in prop_map
		if (prop == 'id') {
			prop = { _label: 'ID', name: 'id' };
		}
		else {
			prop = model.prop_map[prop];
		}

		$('#column_editor .display:first').css('width', 360 * $('#column_editor .display').length + 'px');

		var column_data = {};

		// Renaming a column should not be nested for reference types
		if (!parent) {
			if ($('#column_editor').data('prop') && $('#column_editor').is(':visible')) {
				var col = self.get_columns($('#column_editor'), true);

				// Move the editor to the column node (it will be hidden)
				$('#column_editor').data('column_node').data('column_data', col[0]);
			}

			if (!prop)
				return;

			$('#column_editor').empty();
			$('#column_editor').data('prop', prop.name).data('column_node', column_node);

			column_data = column_node.data('column_data') || {};

			var name_field = new boto_web.ui.forms.text({name: prop.name, _label: '', value: column_data[0] || prop._label});

			$('#column_editor').append(
				$('<label>Rename Column</label>'),
				name_field.field.addClass('rename_column'),
				$('<br class="clear"/>'),
				$('<div class="scrollpane"/>').append(
					$('<div class="display"/>')
				)
			);

			name_field.field.keyup(function(e) {
				if (e.keyCode)
					name_field.field.data('edited', true);
				if (this.value == '')
					name_field.field.data('edited', false);

				var col = column_node.siblings('label');

				if (this.value && this.value != col.text())
					col.html(this.value + ' <small>(was: ' + prop._label + ')</small>');
				else
					col.text(prop._label);
			});

			parent = $('<div class="column"/>').appendTo($('#column_editor .display'));

			$('#column_editor').append(
				$('<br/>'),
				$('<div class="ui-button ui-state-default ui-corner-all"/>')
					.html('<span class="ui-icon ui-icon-disk"></span> Update Column')
					.click(function() {
						self.edit_column(self.model, '');
						$('#column_editor_container').hide();
					}),
				$('<div class="ui-button ui-state-default ui-corner-all"/>')
					.html('<span class="ui-icon ui-icon-closethick"></span> Cancel')
					.click(function() {
						$('#column_editor').empty();
						$('#column_editor_container').hide();
					})
			);

			if (!(prop._item_type in boto_web.env.models))
				$('#column_editor .scrollpane').hide();
		}
		else
			parent = $('<div class="column"/>').appendTo(parent);

		parent.append(
			$('<label>Property name</label><span class="prop_name" title="' + prop.name + '">' + prop._label + '</span><br class="clear"/>' + ((prop._item_type in boto_web.env.models) ? '<label>Property type</label>' + prop._item_type + '<br class="clear"/>' : ''))
		);

		self.node.find('#column_editor_container').show();

		if (prop._item_type in boto_web.env.models) {
			var ref_model = boto_web.env.models[prop._item_type];

			if (prop._type == 'query') {
				parent.append(
					$('<label>Filter this column</label><br class="clear" /><div class="attributes"/><div class="filters"/><br class="clear"/>')
				);

				self.build_attribute_choices(function(e, p) {
					self.add_filter(e, p, null, null, parent);
				}, ref_model, parent);
			}
			else {
				// Empty filters div required to short-circuit filter detection and avoid grabbing a child's filters
				$('<div class="filters hidden"/>').appendTo(parent);
			}

			var prop_choices = $.map(ref_model.properties, function(p) {
				if ($.inArray('read', p._perm) < 0) return null;

				return {text: p._label, value: p.name};
			});

			prop_choices = prop_choices.sort(boto_web.ui.sort_props);

			prop_choices.unshift({text: 'default', value: ''});

			var property_field = new boto_web.ui.forms.dropdown({
				name: prop.name,
				choices: prop_choices
			});

			parent.append(
				$('<label>Display property</label>'),
				property_field.field
					.addClass('sub_prop')
			);

			parent.after(
				$('<div class="display"/>').append(
					$('<div/>')
				)
			);

			property_field.field.change(function() {
				$(this).parents('.display:first').find('.display:first').empty();
				self.edit_column(ref_model, this.value, $(this).parents('.display:first').find('.display:first'));
				if (!$('#column_editor .rename_column:first').data('edited')) {
					$('#column_editor .rename_column:first')
						.val($.map($('#column_editor .prop_name:first, #column_editor .sub_prop option:selected'), function(prop) { return $(prop).text() == 'default' ? null : $(prop).text() }).join(': '))
						.keyup();
				}
			});
		}

		$('#column_editor .scrollpane').scrollTo({top:0, left: '100%'}, 500);

		self.node.find('.sub_prop:first').focus();

		if (column_data[1]) {
			var fill_data = function(col_data, model, base_node) {
				if (!col_data)
					return;

				var prop_names = [model.prop_map[col_data[0]]._label];

				var new_model = boto_web.env.models[model.prop_map[col_data[0]]._item_type];

				if ($.isArray(col_data[1])) {
					if (col_data[1][0]) {
						base_node.find('.sub_prop:first').val(col_data[1][0]).change();
						$.map(fill_data(col_data[1], new_model, base_node.find('.display:first')), function(item) { prop_names.push(item) });
					}
				}
				else if (col_data[1]) {
					base_node.find('.sub_prop:first').val(col_data[1]).change();
				}

				if (new_model && col_data[2]) {
					$.each(col_data[2], function() {
						var prop = new_model.prop_map[this[0]];

						if (this[0] == 'id')
							prop = {_label: 'ID', name: 'id', _perm: ['read'], _type: 'string'};

						self.add_filter(null, prop, this[1], this[2], base_node);
					});
				}

				return prop_names
			};

			var prop_names = fill_data(column_data[1], self.model, $('#column_editor .display:first'));

			name_field.field.val(column_data[0]);

			if (column_data[0] == prop_names.join(': '))
				name_field.field.data('edited', true);
		}
	}


	self.get_link = function(step) {
		var base = ('' + document.location.href).replace(/\?.*|$/, '');

		if (step == 'report') {
			return ('' + document.location.href).replace(/#.*/, '') + '#' + boto_web.env.opts.model_template.replace('*', 'Report');
		}

		if (step > 1)
			return base + '?step=' + step + '&model=' + self.model.name + '&filters=' + escape($.toJSON(self.filters)) + '&columns=' + escape($.toJSON(self.columns)) + '&id=' + (self.obj.id || '');

		return base;
	}

	self.add_breadcrumb = function(step, name){
		var step_link = document.createElement("a");
		step_link.href = self.get_link(step);
		step_link.innerHTML = name;
		var crumb = document.createElement("li");
		$(crumb).append(step_link);
		self.breadcrumbs.append(crumb);
	}
};

