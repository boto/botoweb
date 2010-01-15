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

		self.has_columns = self.columns.length > 0;

		// Add the breadcrumbs
		self.breadcrumbs.empty();
		self.add_breadcrumb(1, "Reporting");
		self.breadcrumbs.append('<li>' + self.model.name + '</li>');

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
		self.add_breadcrumb(2, self.model.name);
		self.breadcrumbs.append('<li>Attributes</li>');

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
				.html('<span></span><span class="ui-icon ui-icon-closethick" onclick="$(this).parent().remove()"></span> <label>' + p._label + '</label><div class="hidden column_editor"></div>')
				.appendTo(self.node.find('ul'))
				.click(function() {
					self.edit_column(self.model, p.name, null, $(this).find('.column_editor'));
				});

			set_sort_icons();

			self.edit_column(self.model, p.name, null, li.find('.column_editor'));
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
					self.node.find('.attribute #' + this[1][0]).parent().click();
				else
					self.node.find('.attribute #' + this[1]).parent().click();
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
		self.add_breadcrumb(2, self.model.name);
		self.add_breadcrumb(3, "Attributes");
		self.breadcrumbs.append('<li>Results</li>');

		$('#next_step').hide();

		self.node.find("#step_4 .results").empty();

		self.query = 'model=' + self.model.name
			+ '&filters=' + escape($.toJSON(self.filters))
			+ '&columns=' + escape($.toJSON(self.columns));

		$("<br/>").addClass("clear").appendTo(self.node.find("#step_4 .results"));

		$('<div/>')
			.addClass('ui-button ui-state-default ui-corner-all')
			.html('<span class="ui-icon ui-icon-refresh"></span>Save Report')
			.click(function() {
				if (self.obj.id) {
					self.obj.properties.query = self.query;
					self.obj.edit({hide: ['query','target_class_name','filters']});
				}
				else
					boto_web.env.models.Report.create({def: {query: self.query}, hide: ['query','target_class_name','filters']});
			})
			.appendTo(self.node.find('#step_4 .results'));
		self.build_results(false, self.node.find("#step_4 .results"));

		setTimeout(function() {
			if (self.obj.id) {
				$("<div/>")
					.addClass('smaller jr')
					.html("<strong>Link to this report:</strong> " + self.get_link(1) + '?id=' + self.obj.id)
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
			try { p = {_label: c[0], name: c[1][0]}; } catch (e) {
				try { p = {_label: c[0], name: c[1]}; } catch (e) {
					try { p = {_label: self.model.prop_map[c]._label, name: c}; } catch (e) {}
				}
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


			if (p.name == 'name') {
				$('<td/>')
					.append(linked_name)
					.appendTo(trbody);
			}
			else if (is_list) {
				$('<td/>')
					.append($('<ul/>').append($('<li/>')
						.attr(boto_web.ui.properties.attribute, p.name)
						.append(is_ref ? linked_name : null)
					))
					.appendTo(trbody);
			}
			else if (is_ref) {
				if ($.isArray(c[1])) {
					var nested_markup = function(prop) {
						var n = $('<span/>')
							.attr(boto_web.ui.properties.attribute, prop[0])

						if (prop.length == 3)
							n.attr(boto_web.ui.properties.filter, $.toJSON(prop[2]));

						if ($.isArray(prop[1]))
							return n.append(nested_markup(prop[1]));
						else if (prop.length > 1)
							return n.append(nested_markup([prop[1] || 'name']))
						else
							return n
					};

					alert($('<td/>')
						.append(nested_markup(c[1]))
						.appendTo(trbody).html());
				}
				else {
					$('<td/>')
						.append(node.append(linked_name))
						.appendTo(trbody);
				}
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

	self.get_columns = function(base_node) {
		if (!base_node)
			base_node = self.node.find('.column_list ul li');

		// Finalize any changes made in the column editor
		//self.edit_column(self.model, '');

		var columns = [];
		base_node.each(function() {
			var query = [];

			// Start with the column name
			query.push($(this).find('.rename_column').val());

			// Reference properties may be nested to change what is displayed
			if ($(this).find('.display .display .display').length) {
				var expand_query = function(prop, parent) {
					var q = [prop];
					var sub_prop = parent.find('.display .sub_prop:first').val() || '';
					var expanded = false;

					if (parent.find('.display .display').length) {
						q.push(expand_query(sub_prop, parent.find('.display:first')));
						expanded = true;
					}
					else {
						q.push(sub_prop);
					}

					// TODO push filtering details
					var filters = self.get_filters(parent);
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

				var sub_prop = $(this).find('.display .sub_prop:first').val() || '';

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

		alert($.dump(columns));

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

		var column_data = {};

		// Renaming a column should not be nested for reference types
		if (!parent) {
			if ($('#column_editor').data('prop')) {
				var col = self.get_columns($('#column_editor'))

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
				$('<br class="clear"/><div class="display"/>')
			);

			name_field.field.keyup(function() {
				var col = column_node.siblings('label');

				if (this.value && this.value != col.text())
					col.html(this.value + ' <small>(was: ' + prop._label + ')</small>');
				else
					col.text(prop._label);
			});

			parent = $('<div/>').appendTo($('#column_editor .display'));
		}
		else
			parent = $('<div/>').appendTo(parent);

		parent.append(
			$('<label>Property Name</label><span class="prop_name" title="' + prop.name + '">' + prop._label + '</span><br class="clear"/>' + ((prop._item_type in boto_web.env.models) ? '<label>Property Type</label>' + prop._item_type + '<br class="clear"/>' : ''))
		);

		if (prop._item_type in boto_web.env.models) {
			var ref_model = boto_web.env.models[prop._item_type];

			if (prop._type == 'query') {
				parent.append(
					$('<label>Filter column</label><br /><div class="attributes"/><div class="filters"/><br class="clear"/>')
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
				$('<div class="display"/>').append(
					$('<div/>').append(
						$('<label>Display property</label>'),
						property_field.field.addClass('sub_prop')
					)
				)
			);

			property_field.field.change(function() {
				$(this).parent().siblings().remove();
				self.edit_column(ref_model, this.value, $(this).parents('.display:first'));
			});
		}

		if (column_data[1]) {
			var fill_data = function(col_data, model, base_node) {
				if (!col_data)
					return;

				var new_model = boto_web.env.models[model.prop_map[col_data[0]]._item_type];

				if ($.isArray(col_data[1])) {
					base_node.find('.sub_prop:first').val(col_data[1][0]).change();
					fill_data(col_data[1], new_model, base_node.find('.display'));
				}
				else if (col_data[1]) {
					base_node.find('.sub_prop:first').val(col_data[1]).change();
				}

				if (new_model && col_data[2]) {
					$(col_data[2]).each(function() {
						var prop = new_model.prop_map[this[0]];

						if (this[0] == 'id')
							prop = {_label: 'ID', name: 'id', _perm: ['read'], _type: 'string'};

						self.add_filter(null, prop, this[1], this[2], base_node);
					});
				}
			};

			fill_data(column_data[1], self.model, $('#column_editor .display'));
		}
	}


	self.get_link = function(step) {
		var base = ('' + document.location.href).replace(/\?.*|$/, '');

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

