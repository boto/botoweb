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

		var has_columns = self.columns.length > 0;

		// Add the breadcrumbs
		self.breadcrumbs.empty();
		self.add_breadcrumb(1, "Reporting");
		self.breadcrumbs.append('<li>' + self.model.name + '</li>');

		if (self.model.properties.length > 10) {
			var blur_text = 'Find an attribute';
			self.narrow_filters = $('<input/>')
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
						self.node.find('.attributes .attribute:visible:eq(0)').click();
						$(input).val('').keyup();
					}
					else if (input.value) {
						self.node.find('.attribute').each(function() {
							if ($(this).text().toLowerCase().indexOf(input.value.toLowerCase()) >= 0)
								$(this).show();
							else
								$(this).hide();
						});
					}
					else {
						self.node.find('.attribute').show();
					}
				})
				.insertBefore(self.node.find('#step_2 .attributes'));
		}

		var add_filter = function(e, property, operator, value) {
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

			// Create a field which allows multiple selections regardless of the item type
			var field = boto_web.ui.forms.property_field(property, {
				allow_multiple: true,
				allow_default: true,
				read_only: false,
				_default_value: value || ''
			});

			$('<div/>')
				.addClass('filter editor ui-button ui-state-default ui-corner-all')
				.appendTo(self.node.find('.filters'))
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
		};

		var get_filters = function() {
			var filter_columns = {name: 1};
			self.filters = [];
			self.node.find('.filter').each(function() {
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

				self.filters.push([prop, op, val]);
			});

			if (!has_columns) {
				self.columns = [];
				for (var prop in filter_columns) {
					self.columns.push(self.model.prop_map[prop]);
				}
			}
		};

		// Add ID to the property list... pushing the properties array does not work
		var props = [{_label: 'ID', name: 'id', _perm: ['read'], _type: 'string'}];
		$(self.model.properties).each(function() { props.push(this); });
		props.sort(boto_web.ui.sort_props)

		$.map(props, function(p) {
			if ($.inArray('read', p._perm) < 0)
				return;

			$('<div/>')
				.addClass('attribute ui-button ui-state-default ui-corner-all')
				.html(p._label)
				.click(function(e) {
					add_filter(e, p)
				})
				.appendTo(self.node.find('#step_2 .attributes'));
		});

		self.node.find("#preview_button").remove();
		$('<div/>')
			.attr("id", "preview_button")
			.addClass('ui-button ui-state-default ui-corner-all')
			.html('<span class="ui-icon ui-icon-refresh"></span>Refresh result preview')
			.click(function() {
				get_filters();
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
				get_filters();
				document.location.href = self.get_link(3);
			})
			.find('em').html('<strong>Modify the report</strong> by choosing the appropriate columns.');

		boto_web.ui.decorate(self.node);

		if (self.filters.length) {
			$(self.filters).each(function() {
				if (this[0] in self.model.prop_map)
					add_filter(null, self.model.prop_map[this[0]], this[1], this[2]);
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

		// Add the breadcrumbs
		self.breadcrumbs.empty();
		self.add_breadcrumb(1, "Reporting");
		self.add_breadcrumb(2, self.model.name);
		self.breadcrumbs.append('<li>Attributes</li>');

		if (self.model.properties.length > 10) {
			var blur_text = 'Find an attribute';
			$('<input/>')
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
						self.node.find('.attributes .attribute:visible:eq(0)').click();
						$(input).val('').keyup();
					}
					if (input.value) {
						self.node.find('label').each(function() {
							if ($(this).text().toLowerCase().indexOf(input.value.toLowerCase()) >= 0) {
								$(this).parent().show()
							}
							else {
								$(this).parent().hide();
							}
						});
					}
					else {
						self.node.find('.attribute').show();
					}
				})
				.insertBefore(self.node.find('#step_3 .attributes'));
		}

		var set_sort_icons = function() {
			if (self.node.find('.column_list li').length > 1) {
				self.node.find('.column_list li span').attr('className', 'ui-icon ui-icon-arrowthick-2-n-s');
				self.node.find('.column_list li:first span').attr('className', 'ui-icon ui-icon-arrowthick-1-s');
				self.node.find('.column_list li:last span').attr('className', 'ui-icon ui-icon-arrowthick-1-n');
			}
			else {
				self.node.find('.column_list li span').attr('className', 'ui-icon ui-icon-bullet');
			}
		};

		var get_columns = function() {
			self.columns = [];
			self.node.find('.column_list ul li').each(function() {
				self.columns.push({name: this.id.replace('column_', ''), _label: $(this).text()});
			});
		}

		// Add ID to the property list... pushing the properties array does not work
		var props = [{_label: 'ID', name: 'id', _perm: ['read'], _type: 'string'}];
		$(self.model.properties).each(function() { props.push(this); });
		props.sort(boto_web.ui.sort_props)

		$(props).each(function() {
			if ($.inArray('read', this._perm) < 0) return;

			var prop = this;

			var container = $('<div/>')
				.addClass('attribute ui-button ui-state-default ui-corner-all')
				.click(function(e) {
					e.stopPropagation();
					$(this).find('input').attr('checked', !$(this).find('input:checked').length).change();
					return false;
				})
				.appendTo(self.node.find('#step_3 .attributes'));

			$('<input/>')
				.attr({id: this.name, value: this._label, type: 'checkbox'})
				.change(function() {
					if ($(this).is(':checked')) {
						$('<li/>')
							.addClass('ui-state-default')
							.attr('id', 'column_' + this.id)
							.html('<span></span>' + this.value)
							.appendTo(self.node.find('ul'))
					}
					else {
						$('.column_list #column_' + this.id).remove();
					}

					set_sort_icons();
				})
				.appendTo(container);
			$('<label/>')
				.attr({'for': this.name})
				.html(' ' + this._label + '<br />')
				.appendTo(container);
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
				get_columns();
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
				get_columns();
				document.location.href = self.get_link(4);
			})
			.find('em').html('<strong>Generate the report</strong> and export the results.');

		if (self.columns) {
			$(self.columns).each(function() {
				self.node.find('.attribute #' + this.name).parent().click();
			});
		}
	}

	self.step_4 = function() {
		if (!self.template) {
			self.template = $(self.node).clone(true);
		}
		self.node.find('article:not(#step_1)').remove();
		self.node.find('#step_1').hide();
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

		$.map(self.columns, function(p) {
			$('<th/>')
				.text(p._label)
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
				$('<td/>')
					.append(node.append(linked_name))
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
			if (RegExp.$3)
				self.columns = $.evalJSON(unescape(RegExp.$3));
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

	self.get_link = function(step) {
		var base = ('' + document.location.href).replace(/\?.*|$/, '');

		if (step > 1)
			return base + '?step=' + step + '&model=' + self.model.name + '&filters=' + escape($.toJSON(self.filters)) + '&columns=' + escape($.toJSON(self.columns)) + '&id=' + self.obj.id;

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
