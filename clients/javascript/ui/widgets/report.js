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
	self.template = $('<div/>').append(self.node.contents().clone());
	self.model = null;
	self.filters = [];
	self.columns = [];

	self.step_1 = function() {
		self.node.find('#step_2, #step_3, #step_4').remove();
		self.filters = [];
		self.columns = [];

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
					self.step_2();
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
		self.node.empty();
		self.template.find('#step_2').clone()
			.appendTo(self.node);

		if (self.model.properties.length > 15) {
			$('<input/>')
				.keyup(function() {
					var input = this;

					if (input.value) {
						self.node.find('.attribute').each(function() {
							if ($(this).text().toLowerCase().indexOf(input.value.toLowerCase()) >= 0)
								$(this).show();
							else
								$(this).hide();
						});
					}
					else {
						self.node.find('.filter').show();
					}
				})
				.appendTo(self.node.find('.attributes'));

			$('<br/>').appendTo(self.node.find('.attributes'));
		}

		var add_filter = function(e, property) {
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
						}),
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
					$(boto_web.ui.forms.property_field(property).field_container)
				)
				.find('.ui-button').remove();
			e.preventDefault();
		};

		var get_filters = function() {
			var filter_columns = {name: 1};
			self.filters = [];
			self.node.find('.filter').each(function() {
				var prop = $(this).find('.property').attr('id').replace('property_', '');
				var op = $(this).find('.operator').val();
				var val = $(this).find('.field_container').data('get_value')();
				op = {'is': '=', 'is not': '!=', 'contains': 'like'}[op] || op;

				if (op == 'like')
					val = '%' + val + '%';
				if (op == 'starts with') {
					val = val + '%';
					op = 'like';
				}
				if (op == 'ends with') {
					val = '%' + val;
					op = 'like';
				}

				if (!filter_columns[prop])
					filter_columns[prop] = 1;

				self.filters.push([prop, op, val]);
			});

			self.columns = [];
			for (var prop in filter_columns) {
				self.columns.push(self.model.prop_map[prop]);
			}
		};

		$.map(self.model.properties.sort(boto_web.ui.sort_props), function(p) {
			if ($.inArray('read', p._perm) < 0) return null;

			$('<div/>')
				.addClass('attribute ui-button ui-state-default ui-corner-all')
				.html(p._label)
				.click(function(e) {
					add_filter(e, p)
				})
				.appendTo(self.node.find('.attributes'));
		});

		$('<div/>')
			.addClass('ui-button ui-state-default ui-corner-all')
			.html('<span class="ui-icon ui-icon-refresh"></span>Refresh result preview')
			.click(function() {
				get_filters();
				self.node.find('.results').empty();
				self.step_4(true);
			})
			.insertBefore(self.node.find('.results'));

		$('<br/>')
			.addClass('clear')
			.appendTo(self.node.find('.results'));

		$('#next_step')
			.show()
			.click(function() {
				get_filters();
				self.step_3();
			})
			.find('em').html('<strong>Modify the report</strong> by choosing the appropriate columns.');

		boto_web.ui.decorate(self.node);
	}

	self.step_3 = function() {
		self.node.empty();
		self.template.find('#step_3').clone()
			.appendTo(self.node);

		if (self.model.properties.length > 15) {
			$('<input/>')
				.keyup(function() {
					var input = this;

					if (input.value) {
						self.node.find('label').each(function() {
							if ($(this).text().toLowerCase().indexOf(input.value.toLowerCase()) >= 0) {
								$(this).show()
								$('#' + $(this).attr('for')).show();
							}
							else {
								$(this).hide();
								$('#' + $(this).attr('for')).hide();
							}
						});
					}
					else {
						self.node.find('label, input').show();
					}
				})
				.appendTo(self.node.find('.attributes'));

			$('<br/>').appendTo(self.node.find('.attributes'));
		}

		var set_sort_icons = function() {
			if (self.node.find('.columns li').length > 1) {
				self.node.find('.columns li span').attr('className', 'ui-icon ui-icon-arrowthick-2-n-s');
				self.node.find('.columns li:first span').attr('className', 'ui-icon ui-icon-arrowthick-1-s');
				self.node.find('.columns li:last span').attr('className', 'ui-icon ui-icon-arrowthick-1-n');
			}
			else {
				self.node.find('.columns li span').attr('className', 'ui-icon ui-icon-bullet');
			}
		};

		var get_columns = function() {
			self.columns = [];
			self.node.find('.columns ul li').each(function() {
				self.columns.push({name: this.id.replace('column_', ''), _label: $(this).text()});
			});
		}

		$(self.model.properties).each(function() {
			if ($.inArray('read', this._perm) < 0) return;

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
						$('#column_' + this.id).remove();
					}

					set_sort_icons();
				})
				.appendTo(self.node.find('.attributes'));
			$('<label/>')
				.attr({'for': this.name})
				.html(' ' + this._label + '<br />')
				.appendTo(self.node.find('.attributes'));
		});

		$('<ul/>')
			.sortable({
				stop: function() {
					set_sort_icons();
				}
			})
			.disableSelection()
			.appendTo(self.node.find('.columns'));

		$('<div/>')
			.addClass('ui-button ui-state-default ui-corner-all')
			.html('<span class="ui-icon ui-icon-refresh"></span>Refresh result preview')
			.click(function() {
				get_columns();
				self.node.find('.results').empty();
				self.step_4(true);
			})
			.insertBefore(self.node.find('.results'));

		$('<br/>')
			.addClass('clear')
			.appendTo(self.node.find('.results'));

		$('#next_step')
			.show()
			.unbind()
			.click(function() {
				get_columns();
				self.query = '?model=' + self.model.name
					+ '&filters=' + escape($.toJSON(self.filters))
					+ '&columns=' + escape($.toJSON(self.columns));
				self.step_4();
				document.location.href += self.query;
			})
			.find('em').html('<strong>Generate the report</strong> and export the results.');
	}

	self.step_4 = function(preview) {
		if (!preview) {
			self.node.empty();
			self.template.find('#step_4').clone()
				.appendTo(self.node);

			$('#next_step').hide();

			$('<div/>')
				.addClass('ui-button ui-state-default ui-corner-all')
				.html('<span class="ui-icon ui-icon-refresh"></span>Save Report')
				.click(function() {
					var editor = boto_web.env.models.Report.create({def: {query: self.query}, hide: ['query']});
				})
				.appendTo(self.node.find('.results'));
		}

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
			$('<td/>')
				.text(' ')
				.attr('bwAttribute', p.name)
				.appendTo(trbody);
		});

		$('<table/>')
			.append(thead)
			.append(tbody)
			.appendTo(self.node.find('.results'));

		self.results = new boto_web.ui.widgets.SearchResults(tbody, self.model);

		self.model.query(self.filters, function(data, page) {
			self.results.update(data, page);
			return !preview;
		});
	}

	self.update = function() {
		if (/model=(.*?)&filters=(.*?)&columns=(.*?)(&|$)/.test(document.location.href)) {
			self.query = RegExp.lastMatch;
			self.model = boto_web.env.models[RegExp.$1];
			self.filters = $.evalJSON(unescape(RegExp.$2));
			self.columns = $.evalJSON(unescape(RegExp.$3));
			self.step_4();
		}
		else if (/step=(\d+)/.test(document.location.href)) {
			self['step_' + RegExp.$1]();
		}
		else {
			self.step_1();
		}
	}

	self.update();
};
