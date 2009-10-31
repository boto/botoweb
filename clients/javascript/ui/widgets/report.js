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
	self.template = self.node.contents().clone();
	self.model = null;
	self.properties = [];

	self.step_1 = function() {
		self.node.empty();

		$('<h2/>')
			.text('Step 1: Choose the foundation of the report')
			.appendTo(self.node);

		var choices = $('<select/>')
			.appendTo(self.node);

		for (var name in boto_web.env.models) {
			$('<option/>')
				.attr({value: name, text: name})
				.appendTo(choices);
		}

		$('<a/>')
			.addClass('ui-button ui-state-default ui-corner-all')
			.html('<span class="ui-icon ui-icon-arrowthick-1-e"></span>Done')
			.click(function() {
				self.model = boto_web.env.models[choices.val()];
				self.step_2();
			})
			.appendTo(self.node);
	}

	self.step_2 = function() {
		self.node.empty();

		$('<h2/>')
			.text('Step 2: Choose the attributes to include in the report')
			.appendTo(self.node);

		$('<p/>')
			.html('To find attributes more quickly, simply type a portion of the property you want to find in the box below.')
			.appendTo(self.node);

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
			.appendTo(self.node);

		$('<br/>').appendTo(self.node);

		$(self.model.properties).each(function() {
			$('<input/>')
				.attr({id: this.name, value: this._label, type: 'checkbox'})
				.appendTo(self.node);
			$('<label/>')
				.attr({'for': this.name})
				.html(' ' + this._label + '<br />')
				.appendTo(self.node);
		});

		$('<a/>')
			.addClass('ui-button ui-state-default ui-corner-all')
			.html('<span class="ui-icon ui-icon-arrowthick-1-e"></span>Done')
			.click(function() {
				self.node.find('input').each(function() {
					if (this.checked) {
						self.properties.push({name: this.id, label: this.value});
					}
				});
				self.step_3();
			})
			.appendTo(self.node);
	}

	self.step_3 = function() {
		self.node.empty();

		$('<h2/>')
			.text('Results')
			.appendTo(self.node);

		$('<p/>')
			.text('Use the buttons at the top of the table to generate a CSV or Excel spreadsheet from these results.');

		var thead = $('<thead/>');
		var tbody = $('<tbody/>')
			.attr('bwDefault', 'all');
		var trhead = $('<tr/>').appendTo(thead);
		var trbody = $('<tr/>')
			.addClass('bwObject')
			.appendTo(tbody);

		$(self.properties).each(function() {
			$('<th/>')
				.text(this.label)
				.appendTo(trhead);
			$('<td/>')
				.attr('bwAttribute', this.name)
				.text(' ')
				.appendTo(trbody);
		});

		$('<table/>')
			.append(thead)
			.append(tbody)
			.appendTo(self.node);


		new boto_web.ui.widgets.SearchResults(tbody, self.model);
	}

	self.step_1();
};
