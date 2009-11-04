/**
 * @author    Ian Paterson
 * @namespace boto_web.ui.widgets.search_results
 */

/**
 * Displays templated search results.
 *
 * @param node the node containing the search result template.
 */
boto_web.ui.widgets.DateTime = function(node) {
	var self = this;

	self.node = $(node);
	var t = self.node.text().match(/(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)/);
	self.date_time = new Date(Date.UTC(t[1],t[2],t[3],t[4],t[5],t[6]));
	self.node.empty();
	self.node.text(self.date_time.toLocaleString().replace(/^\w+ /,''));
};