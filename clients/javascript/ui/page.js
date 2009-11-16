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

	self.get_link = function(method, model) {
		var base_url = document.location.href + '';
		base_url = base_url.replace(/action=.*?(&|$)/,'');
		if (base_url.indexOf('?') == -1)
			base_url += '?';
		else
			base_url += '&';

		switch (method) {
			case 'create':
				return base_url + 'action=create/' + model.name;
				break;
		}
	};

	self.node
		.attr('id', '');
	self.node = $('<div/>')
		.attr({
			id: self.id,
			bwModel: self.node.attr('bwModel')
		})
		.append(self.node);

	self.parse_markup = function() {
		if (!self.node.children().length)
			return;

		for (var sel in boto_web.env.opts.markup) {
			self.node.find(sel).each(boto_web.env.opts.markup[sel]);
		}

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

		// Add links
		sel = boto_web.ui.selectors.link;
		prop =  boto_web.ui.properties.link;

		self.node.find(sel).each(function() {
			// Translate
			var val = $(this).attr(prop);
			var data;
			if (/(.*)\((.*)\)/.test(val)) {
				val = RegExp.$1;
				data = RegExp.$2;
			}

			var method = {'create':'post'}[val];

			var model = '';

			if ($(this).is(boto_web.ui.selectors.model))
				model = $(this).attr(boto_web.ui.properties.model);
			else
				model = $(this).parents(boto_web.ui.selectors.model + ':eq(0)').attr(boto_web.ui.properties.model);

			model = boto_web.env.models[model] || '';

			// Only allow create, and only if that action is allowed
			// according to the model API.
			if (!model || !(method && method in model.methods)) {
				if (model)
					$(val).log(model.name + ' does not support this action');
				return;
			}

			// Get defaults for the create form.
			if (data) {
				// Do not eval defaults if the JSON string references object values
				if (!/:\s*([a-z_]\w*)\s*(,|\})/i.test(data)) {
					eval('data = ' + data);
					$(this).click(function(e) {
						model.create({def: data});
						e.preventDefault();
					})
				}
			}

			$(this).attr('href', self.get_link(val, model));
		});

		// Hide content based on user's auth_group
		// TODO add this to some event that can be triggered when content on the page changes
		self.node.find('.auth').each(function() {
			var authorized = true;
			var node = $(this);

			if (node.hasClass('deny-all')) {
				authorized = false;
				$(boto_web.env.user.groups).each(function() {
					if (node.hasClass('allow-' + this.name))
						authorized = true;
				});
			}
			else {
				$(boto_web.env.user.groups).each(function() {
					if (node.hasClass('deny-' + this.name))
						authorized = false;
				});
			}
			// Avoid processing the same item again
			node.removeClass('auth');
			if (!authorized)
				node.empty().remove();
		});
	}

	if (self.id in boto_web.ui.desktop.pages) {
		return boto_web.ui.desktop.pages[self.id];
	}

	self.activate = function() {
		boto_web.ui.desktop.activate(self);
	}

	if (self.node.find('h1'))
		self.title = self.node.find('h1').text();
	document.title = self.title || document.title;

	// Load templates
	var sel = boto_web.ui.selectors.template;
	var prop =  boto_web.ui.properties.template;
	var templates;
	var num_templates = 0;

	// Map each template to a list of nodes where it should be inserted
	self.node.find(sel).each(function() {
		var val = $(this).attr(prop);
		if (!templates)
			templates = {};

		if (!templates[val]) {
			num_templates++;
			templates[val] = [];
		}

		templates[val].push(this);
	});

	// All templates must be loaded before parsing the resulting markup
	if (!templates)
		self.parse_markup();
	else {
		for (var template in templates) {
			$.get(template, null, function(nodes) { return function(html) {
				$(nodes).each(function() {
					$(this).append(html);
				});

				// When all templates are done, parse the resulting markup
				if (--num_templates == 0)
					self.parse_markup();

			}}(templates[template]));
		}
	}
};
