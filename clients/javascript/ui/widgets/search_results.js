/**
 * @author    Ian Paterson
 * @namespace boto_web.ui.widgets.search_results
 */

/**
 * Displays templated search results.
 *
 * @param node the node containing the search result template.
 */
boto_web.ui.widgets.SearchResults = function(node, model) {
	var self = this;

	self.node = $(node);
	self.model = model;
	self.template = self.node.find(boto_web.ui.selectors.object)
		.addClass('object')
		.clone();
	self.node.empty();
	self.node.parent('table').hide();
	self.def = self.node.attr(boto_web.ui.properties.def);

	self.update = function(results, append) {
		self.node.parent('table').show();
		if (!self.data_table)
			self.data_table = new boto_web.ui.widgets.DataTable(self.node.parent('table'));

		for (var i in results) {
			self.data_table.append(new boto_web.ui.Object(self.template.clone(), self.model, results[i]).node);
		}
	}

	self.reset = function() {
		self.data_table.reset();
	}

	if (self.def == 'all') {
		self.model.all(function(results, page) { self.update(results, page); return page < 10; });
	}
	else if (self.def) {
		// Evaluate JSON search filters
		eval('self.def = ' + self.def);

		if ($.isArray(self.def))
			self.model.query(self.def, function(results, page) { self.update(results, page); });
		else
			self.model.find(self.def, function(results, page) { self.update(results, page); });
	}

};
