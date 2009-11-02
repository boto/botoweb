/**
 * @author    Ian Paterson
 * @namespace boto_web.ui.page
 */

/**
 * A page with botoweb markup.
 *
 * @param html an HTML document fragment for parsing.
 */
boto_web.ui.Page = function(html) {
	var self = this;

	self.node = $(html).is(boto_web.ui.selectors.section) ? $(html) : $(html).find(boto_web.ui.selectors.section);
	self.id = self.node.attr('id') || 'section_' + boto_web.ui.desktop.num_pages;

	if (self.id in boto_web.ui.desktop.pages) {
		// TODO trigger a real event
		if ('listener' in boto_web.ui.desktop.pages[self.id])
			boto_web.ui.desktop.pages[self.id].listener.update();
		return boto_web.ui.desktop.pages[self.id];
	}

	self.node
		.attr('id', '');
	self.node = $('<div/>')
		.attr({
			id: self.id,
			bwModel: self.node.attr('bwModel')
		})
		.append(self.node);

	if (self.node.attr(boto_web.ui.properties.model)) {
		self.node.find(boto_web.ui.selectors.object).each(function() {
			var model = boto_web.env.models[self.node.attr(boto_web.ui.properties.model)];
			var node = this;
			var id = boto_web.ui.params.id;

			self.id = model.name + '_' + id;

			$(node).hide();

			model.get(id, (function(action) { return function(obj) {
				self.obj = new boto_web.ui.Object(node, model, obj, action);
				$(node).show();

				self.title = self.node.find('h1').text();
				document.title = self.title || document.title;
			};})(RegExp.$2));
		});
	}
	else {
		self.node.find(boto_web.ui.selectors.search).each(function() {
			new boto_web.ui.widgets.Search(this);
		});

		self.node.find(boto_web.ui.selectors.report).each(function() {
			self.listener = new boto_web.ui.widgets.Report(this);
		});
	}

	if (self.id in boto_web.ui.desktop.pages) {
		return boto_web.ui.desktop.pages[self.id];
	}

	self.activate = function() {
		boto_web.ui.desktop.activate(self);
	}

	self.title = self.node.find('h1').text();
	document.title = self.title || document.title;
};
