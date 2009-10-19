/**
 * @author    Ian Paterson
 * @namespace boto_web.ui.widgets.search
 */

/**
 * Generates a search form.
 *
 * @param node the node containing the search parameters.
 */
boto_web.ui.widgets.Search = function(node) {
	var self = this;

	self.node = $(node).addClass('widget-search');
	self.header = self.node.find(boto_web.ui.selectors.header);
	self.model = boto_web.env.models[self.node.attr(boto_web.ui.properties.model)];
	self.results = new boto_web.ui.widgets.SearchResults(self.node.find(boto_web.ui.selectors.search_results), self.model);
	self.props = self.node.attr(boto_web.ui.properties.attributes) || 'all';
	self.fields = [];

	if (self.props != 'all')
		self.props = self.props.split(',');

	// Find any properties matching the search parameters
	self.props = $.grep(self.model.properties, function(obj) {
		return self.props == 'all' || $.inArray(obj.name, self.props) >= 0
	});

	$('<h2/>')
		.text('Search')
		.appendTo(self.header);

	for (var i in self.props) {
		var prop = self.props[i];
		var field;

		switch (prop._type) {
			case 'string':
			case 'integer':
			case 'password':
			case 'list':
				if (prop.choices)
					field = new boto_web.ui.dropdown(prop)
						.read_only(false);
				else if (prop.maxlength > 1024)
					field = new boto_web.ui.textarea(prop)
						.read_only(false);
				else
					field = new boto_web.ui.text(prop)
						.read_only(false);
				break;
			case 'dateTime':
				field = new boto_web.ui.date(prop)
						.read_only(false);
				break;
			case 'object':
				field = new boto_web.ui.picklist(prop)
						.read_only(false);
				break;
		}

		if (!field)
			continue;

		$(field.node).appendTo(self.header);
		self.fields.push(field);
	}

	self.submit = function() {
		var query = [];

		$(self.fields).each(function() {
			var val;

			if (this.fields.length > 1) {
				val = [];
				$(this.fields).each(function() {
					val.push(this.val());
				});
			}
			else
				val = this.field.val();

			query.push([this.field.attr('name'), 'like', '%' + val + '%']);
		});

		self.model.query(query, function(data) {
			if (data.length) {
				self.results.update(data);
			}
			else {
				boto_web.ui.alert('The search did not return any results.');
			}
			// TODO data save callback
		});
	};

	$('<a/>')
		.attr('href', '#')
		.addClass('ui-button ui-state-default ui-corner-all')
		.html('<span class="ui-icon ui-icon-search"></span>Search')
		.click(function(e) {
			e.preventDefault();
			self.submit();
		})
		.appendTo($('<div><label>&nbsp;</label></div>').appendTo(self.header));

	$('<br/>')
		.addClass('clear')
		.appendTo(self.header);
};
