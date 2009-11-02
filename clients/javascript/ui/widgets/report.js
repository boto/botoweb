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
		self.node.empty();

		self.template.find('#step_1').clone()
			.appendTo(self.node);

		/*var choices = $('<select/>')
			.appendTo(self.node.find('.new_report'));*/

		for (var name in boto_web.env.models) {
			/*$('<option/>')
				.attr({value: name, text: name})
				.appendTo(choices);*/
			$('<div/>')
				.addClass('ui-button ui-state-default ui-corner-all')
				.html('<strong>' + name + '</strong>')
				.click(function() {
					self.model = boto_web.env.models[name];
					self.step_2();
				})
				.appendTo(self.node.find('.new_report'))
				.each(function() {
					var seen = {};
					var links = $.map(boto_web.env.models[name].properties, function(p){
						if (p._type == 'reference' && !seen[p._item_type]) {
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
		}

		/*$('<div/>')
			.addClass('ui-button ui-state-default ui-corner-all')
			.html('<span class="ui-icon ui-icon-arrowthick-1-e"></span>Next')
			.click(function() {
				self.model = boto_web.env.models[choices.val()];
				self.step_2();
			})
			.appendTo(self.node.find('.new_report'));*/
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

		var add_filter = function(e, property) {
			$('<div/>')
				.addClass('filter')
				.appendTo(self.node.find('.filters'))
				.append(
					$('<select/>')
						.addClass('property')
						.each(function() {
							var select = this;
							$(self.model.properties.sort(function(a,b) {
								return a._label.toLowerCase() > b._label.toLowerCase() ? 1 : -1;
							})).each(function() {
								$('<option/>').attr({text: this._label, value: this.name}).appendTo(select);
							})
						})
						.val(property),
					$('<select/>')
						.addClass('operator')
						.each(function() {
							var select = this;
							$(['is', 'is not', 'contains', 'starts with', 'ends with', '>', '<', '>=', '<=']).each(function() {
								$('<option/>').attr({text: this, value: this}).appendTo(select);
							})
						}),
					$('<input/>')
						.attr('type', 'text')
						.keydown(function(e) {
							if (e.keyCode == 40)
								add_filter(e);
						}).focus()
				);
			e.preventDefault();
		};

		var get_filters = function() {
			var filter_columns = {name: 1};
			self.filters = [];
			self.node.find('.filter').each(function() {
				var prop = $(this).find('.property').val();
				var op = $(this).find('.operator').val();
				var val = $(this).find('input').val();
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

		$.map(self.model.properties, function(p) {
			if ($.inArray('read', p._perm) < 0) return null;

			$('<div/>')
				.addClass('ui-button ui-state-default ui-corner-all')
				.html(p._label)
				.click(function(e) {
					add_filter(e, p.name)
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
			.appendTo(self.node.find('.filters'));

		$('<div/>')
			.addClass('ui-button ui-state-default ui-corner-all')
			.html('<span class="ui-icon ui-icon-arrowthick-1-e"></span>Next')
			.click(function() {
				get_filters();

				self.step_3();
			})
			.appendTo(self.node.find('.filters'));

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
			.html('<span class="ui-icon ui-icon-arrowthick-1-e"></span>Next')
			.click(function() {
				self.columns = [];
				self.node.find('.columns ul li').each(function() {
					self.columns.push({name: this.id.replace('column_', ''), _label: $(this).text()});
				});
				self.step_4();
			})
			.appendTo(self.node.find('.columns'));
	}

	self.step_4 = function(preview) {
		if (!preview) {
			self.node.empty();
			self.template.find('#step_4').clone()
				.appendTo(self.node);
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
			self.results.update(data, !preview);
			return true;
		});
	}

	self.step_1();
};
