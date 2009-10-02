/**
 * @projectDescription This is an experimental and unfinished JavaScript
 * library which will be capable of generating a full CRUD interface based on
 * a boto_web environment.
 *
 * @author    Ian Paterson
 * @namespace boto_web.ui.js
 */

/**
 * CRUD interface for simplified web application implementation based on a
 * boto_web environment.
 */
boto_web.ui = {
	/**
	 * Initializes the boto_web interface.
	 *
	 * @param {boto_web.Environment} env The current boto_web environment.
	 */
	init: function(env) {
		var self = boto_web.ui;

		self.node = $('<div/>')
			.addClass('boto_web')
			.appendTo('body');
		self.header = $('<div/>')
			.addClass('header')
			.appendTo(self.node);
		self.heading = $('<h1/>')
			.text('Database Management')
			.appendTo(self.header);
		self.nav = $('<ul/>')
			.addClass('nav')
			.appendTo(self.header);
		self.content = $('<div/>')
			.attr({id: 'content'})
			.appendTo(self.node);

		self.pages = {};

		// Merge homepage as a generated false model
		$.each($.merge([{obj: {href: 'home', name: 'Home', home: 1}}], env.routes), function() {
			var model = this.obj;

			if (typeof this.obj == 'string')
				model = env.models[this.obj];

			model.page = new boto_web.ui.Section(model, env);
			$('<a/>')
				.attr({href: '#' + this.href})
				.text(model.name)
				.appendTo($('<li/>').appendTo(self.nav));

			self.pages[model.href] = model.page;
		});
	},

	Section: function(model, env) {
		var self = this;

		self.model = model;
		self.href = self.model.href;
		self.name = 'Database Management' + ((model.home) ? '' : ' &ndash; ' + self.model.name);

		self.node = $('<div/>')
			.attr({id: self.model.href.replace(/\//g, '_')})
			.text('Unfinished content placeholder for ' + self.model.name + ' page.')
			.addClass('page')
			.load(function() { boto_web.ui.heading.html(self.name) })
			.hide()
			.appendTo(boto_web.ui.node);
		self.content = $('<div/>')
			.attr({id: self.model.href.replace(/\//g, '_') + '_main'})
			.addClass('content')
			.appendTo(self.node);
		self.sub_pages = {};

		self.switch_mode = function(mode) {
			switch (mode) {
				case 'post':
					self.model.ui_create();
					break;
				case 'put':
					self.model.get(prompt('Please enter the ID of the object you wish to edit'), function(obj) {
						obj.ui_edit();
					});
					break;
				case 'get':
					self.model.all(function(obj) {
						self.sub_pages[mode].html('<pre>' + $.dump($.map(obj, function(o) { return o.properties.id + ': ' + o.properties.name })) + '</pre>')
					});
					break;
			}
		}

		for (var i in self.model.methods) {
			switch (i) {
				case 'put':
				case 'post':
				case 'get':
					$('<a/>')
						.attr({href: '#' + self.href + '/' + i})
						.text(self.model.methods[i])
						.addClass('button')
						.appendTo(self.content)
				default:
					self.sub_pages[i] = $('<div/>')
						.attr({id: self.model.href.replace(/\//g, '_') + '_' + i})
						.text('Please wait, loading.')
						.addClass('content')
						.hide()
						.load(function(mode) { return function() { self.switch_mode(mode) } }(i))
						.appendTo(self.node)
			}
		}
	},

	BaseModelEditor: function(model, obj, opts) {
		var self = this;

		self.node = $('<div/>')
			.addClass('content')
			.appendTo(model.page.node);

		model.page.node.show();

		self.properties = model.properties;
		self.obj = obj;
		self.model = model;
		self.fields = [];

		$(self.properties).each(function() {
			var props = this;

			if (typeof obj != 'undefined')
				props = $.extend(this, {value: obj.properties[this.name]});

			var field;

			switch (this._type) {
				case 'string':
				case 'integer':
				case 'list':
					if (this.choices)
						field = new boto_web.ui.dropdown(props)
							.read_only(false);
					else
						field = new boto_web.ui.text(props)
							.read_only(false);
					break;
				case 'dateTime':
					field = new boto_web.ui.date(props)
						.read_only(false);
					break;
				case 'object':
					field = new boto_web.ui.picklist(props)
						.read_only(false);
					break;
			}

			if (typeof field == 'undefined') return;

			self.fields.push(field);
			field.node.appendTo(self.node)
		});

		self.submit = function() {
			var self = this;
			var data = {};

			if (self.obj)
				data.id = self.obj.id;

			$(self.fields).each(function() {
				data[this.field.attr('name')] = this.field.val();
			});

			self.model.save(data, function(data) {

				alert(data.status);
				// TODO data save complete callback
			});
		};

		$('<br/>')
			.addClass('clear')
			.appendTo(self.node);

		$('<input/>')
			.attr({type: 'button'})
			.val('Update')
			.addClass('button')
			.click(function() { self.submit() })
			.appendTo(self.node);
	},


	/**
	 * Generic interface for all field types.
	 *
	 * @param {Object} properties HTML node properties.
	 */
	_field: function(properties) {
		var self = this;
		this.node = $('<div/>');
		this.label = $('<label/>').html(properties._label || '&nbsp;');
		this.field = $('<' + (properties._tagName || 'input') + '/>');
		this.text = $('<span/>');

		properties.id = properties.id || 'field_' + properties.name;

		for (p in properties) {
			var v = properties[p];

			if (p.indexOf('_') == 0)
				continue;

			switch (p) {
				case 'choices':
					for (i in v) {
						v[i].text = v[i].text || v[i].value;
						var opt = $('<option/>').attr(v[i]);

						this.field.append(opt)
					}
					break;
				default:
					this.field.attr(p, v);
			}
		}

		if (properties._default) {
			this.field.val(properties._default);
		}

		this.text.text(this.field.val());

		/**
		 * Switches the
		 */
		this.read_only = function(on) {
			if (on || typeof on == 'undefined') {
				this.field_container.hide();
				this.text.show();
			}
			else {
				this.text.hide();
				this.field_container.show();
			}

			return this;
		}

		this.field_container = $('<span/>').addClass('field_container').append(this.field);
		this.node.append(this.label, this.field_container, this.text);
		this.read_only();
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	textarea: function(properties) {
		properties.innerHTML = properties.value;
		boto_web.ui._field.call(this, properties);
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	text: function(properties) {
		if (/password/.test(properties.name))
			properties.type = 'password';

		boto_web.ui._field.call(this, properties);

		if (properties._type == 'list') {
			$('<div />').text('Add').appendTo(this.field_container)
		}
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	dropdown: function(properties) {
		properties._tagName = 'select';
		boto_web.ui._field.call(this, properties);
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	date: function(properties) {
		boto_web.ui._field.call(this, properties);

		this.datepicker = $(this.field).datepicker({
			showOn: 'both',
			showAnim: 'slideDown'
		});

	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	picklist: function(properties) {
		properties.value = '[will eventually be a picklist]';
		boto_web.ui._field.call(this, properties);

		if (properties._type == 'list') {
			this.field.attr({cols: 5, multiple: 'multiple'});
		}
	}
};

boto_web.ModelMeta.prototype.ui_create = function(opts) { return boto_web.ui.BaseModelEditor(this, undefined, opts); };

boto_web.Model.prototype.ui_edit = function(opts) { return boto_web.ui.BaseModelEditor(boto_web.env.models[this.name], this, opts); };