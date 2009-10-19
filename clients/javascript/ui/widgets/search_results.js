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

	self.update = function(results) {
		self.node.empty();

		for (var i in results) {
			self.node.append(new boto_web.ui.Object(self.template.clone(), self.model, results[i]).node);
		}

		self.node.parent('table').dataTable();

		// Hide details
		sel = boto_web.ui.selectors.details;

		self.node.find(sel).each(function() {
			$(this).find('.widget-attribute_list').hide();
		});
	}

	if (self.node.attr(boto_web.ui.properties.def) == 'all') {
		self.model.all(function(results) { self.update(results) });
	}

};
