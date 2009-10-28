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

	self.update = function(results) {
		self.node.empty();
		self.node.parent('table').show();

		for (var i in results) {
			self.node.append(new boto_web.ui.Object(self.template.clone(), self.model, results[i]).node);
		}

		if (self.data_table) {
			self.data_table.refresh();
			return;
		}

		self.data_table = new boto_web.ui.widgets.DataTable(self.node.parent('table'));
	}

	if (self.def == 'all') {
		self.model.all(function(results) { self.update(results); });
	}
	else if (self.def) {
		// Evaluate JSON search filters
		eval('self.def = ' + self.def);

		if ($.isArray(self.def))
			self.model.query(self.def, function(results) { self.update(results); });
		else
			self.model.find(self.def, function(results) { self.update(results); });
	}

};
