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
	self.props = [];
	self.fields = [];

	self.get_link = function(method) {
		var base_url = document.location.href + '';
		base_url = base_url.replace(/\?.*/,'');
		switch (method) {
			case 'post':
				return base_url + '?action=create/' + self.model.name;
				break;
		}
	};

	// Find any properties matching the search parameters
	$((self.node.attr(boto_web.ui.properties.attributes) || 'all').split(',')).each(function() {
		if (this == 'all') {
			self.props.push(self.model.properties);
			return;
		}
		var name = this;
		var prop = $.grep(self.model.properties, function(p) {
			return p.name == name;
		});

		if (prop)
			self.props.push(prop[0]);
	});

	// Add editing tools
	sel = boto_web.ui.selectors.editing_tools;

	self.node.find(sel).each(function() {
		new boto_web.ui.widgets.EditingTools(this, self.model, 'create');
	});

	// Add links
	sel = boto_web.ui.selectors.link;
	prop =  boto_web.ui.properties.link;

	self.node.find(sel).each(function() {
		// Translate
		var val = $(this).attr(prop);
		var method = {'create':'post'}[val];

		// Only allow create, and only if that action is allowed
		// according to the model API.
		if (!(method && method in self.model.methods)) {
			$(val).log(self.model.name + ' does not support this action');
			return;
		}

		$(this).attr('href', self.get_link(method));
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

	$(self.header).find('input').keyup(function(e) {
		if (e.keyCode == 13)
			self.submit();
	});

	self.submit = function() {
		var query = [];

		$(self.fields).each(function() {
			var val;

			if (this.fields.length > 1) {
				val = [];
				$(this.fields).each(function() {
					if (this.val())
						val.push(this.val());
				});
			}
			else
				val = this.field.val();

			if (val)
				query.push([this.field.attr('name'), 'like', '%' + val + '%']);
		});

		self.model.query(query, function(results, page) {
			if (results.length) {
				self.results.reset();
				self.results.update(results, page);

				return page < 10;
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
