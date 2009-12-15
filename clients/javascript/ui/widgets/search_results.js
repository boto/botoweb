/**
 * @author    Ian Paterson
 * @namespace boto_web.ui.widgets.search_results
 */

/**
 * Displays templated search results.
 *
 * @param node the node containing the search result template.
 */
boto_web.ui.widgets.SearchResults = function(node, model, opts) {
	var self = this;

	self.node = $(node);
	self.model = model;
	self.template = self.node.find(boto_web.ui.selectors.object)
		.addClass('object')
		.clone();
	self.node.empty();
	self.def = self.node.attr(boto_web.ui.properties.def);
	self.limit_pages = self.node.attr("bwLimit");
	self.opts = opts || { };
	self.num_results = 0;

	self.update = function(results, append, count) {
		if (!results || results.length == 0)
			return;

		var nodes = [];
		var objects = [];
		for (var i in results) {
			self.num_results++;
			var o = new boto_web.ui.Object(self.template.clone(), boto_web.env.models[results[i].properties.model], results[i]);
			nodes.push(o.node);
			objects.push(o);
		}

		if (self.data_table) {
			if (count) {
				if (count > 50) {
					self.opts.min_memory = true;
				}
				self.data_table.update_progress(100 * self.num_results / count, 'Total ' + count + ' results');
			}

			self.data_table.opts.no_redraw = self.opts.min_memory;

			var indices = self.data_table.append(nodes);

			$(indices).each(function (i, row) {
				if (!(objects[i].obj.id in self.model.data_tables))
					self.model.data_tables[objects[i].obj.id] = [];

				var t = {
					table: self.data_table,
					row: row
				};

				objects[i].data_tables.push(t);
				self.model.data_tables[objects[i].obj.id].push(t);
			});
		}
		else
			$(nodes).each(function() { self.node.append(this); });
	}

	self.reset = function() {
		if (self.data_table)
			self.data_table.reset();
		self.num_results = 0;
	}

	if (self.def == 'all') {
		self.model.all(function(results, page, count) { self.update(results, page, count); return ((self.limit_pages == "none") || (page < eval(self.limit_pages) )); });
	}
	else if (self.def) {
		// Evaluate JSON search filters
		eval('self.def = ' + self.def);

		if ($.isArray(self.def))
			self.model.query(self.def, function(results, page, count) { self.update(results, page, count); return ((self.limit_pages == "none") || (page < eval(self.limit_pages))); });
		else
			self.model.find(self.def, function(results, page, count) { self.update(results, page, count); return ((self.limit_pages == "none") || (page < eval(self.limit_pages))); });
	}

	if (self.node.is('tr, tbody')) {
		setTimeout(function() {
			self.data_table = new boto_web.ui.widgets.DataTable(self.node.parent('table'));
		}, 10);
	}
	else if (self.node.is('table')) {
		setTimeout(function() {
			self.data_table = new boto_web.ui.widgets.DataTable(self.node);
		}, 10);
	}
};
