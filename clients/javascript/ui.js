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
			.text('')
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
			self.sub_pages[mode].html('');

			switch (mode) {
				case 'post':
					self.sub_pages[mode].append(self.model.ui_create().node);
					break;
				case 'put':
					self.model.get(prompt('Please enter the ID of the object you wish to edit'), function(obj) {
						self.sub_pages[mode].append(obj.ui_edit().node);
					});
					break;
				case 'get':
					self.model.all(function(obj) {
						$(obj).each(function() {
							self.sub_pages[mode].append(this.ui_display().node)
						});
						if (obj.length == 0)
							self.sub_pages[mode].html('<h2>No results found</h2>');
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

		if (!opts)
			opts = {};

		opts = $.extend({read_only: false}, opts);

		self.node = $('<div/>')
			.addClass('editor')
			.addClass(model.name);

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
				case 'password':
				case 'list':
					if (this.choices)
						field = new boto_web.ui.dropdown(props)
							.read_only(opts.read_only);
					else if (props.maxlength > 1024)
						field = new boto_web.ui.textarea(props)
							.read_only(opts.read_only);
					else
						field = new boto_web.ui.text(props)
							.read_only(opts.read_only);
					break;
				case 'dateTime':
					field = new boto_web.ui.date(props)
						.read_only(opts.read_only);
					break;
				case 'object':
					field = new boto_web.ui.picklist(props)
						.read_only(opts.read_only);
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
				var val;

				if (this.fields.length > 1) {
					val = [];
					$(this.fields).each(function() {
						val.push(this.val());
					});
				}
				else
					val = this.field.val();

				data[this.field.attr('name')] = val;
			});

			self.model.save(data, function(data) {
				if (data.status < 300) {
					alert('The database has been updated.');
					$(self.node).slideUp();
				}
				else {
					alert('There was an error updating the database.');
				}
				// TODO data save callback
			});
		};

		$('<br/>')
			.addClass('clear')
			.appendTo(self.node);

		if (!opts.read_only) {
			$('<input/>')
				.attr({type: 'button'})
				.val('Save')
				.addClass('button')
				.click(function() { self.submit() })
				.appendTo(self.node);
		}

		$('<input/>')
			.attr({type: 'button'})
			.val('Cancel')
			.addClass('button')
			.click(function() { $(self.node).slideUp(); })
			.appendTo(self.node);
	},


	BaseModelDisplay: function(model, obj, opts) {
		var self = this;

		self.node = $('<div/>')
			.addClass('object')
			.addClass(model.name);

		var display_value = obj.properties.name || obj.properties[model.properties[0].name];

		if (!display_value) {
			$(obj.properties).each(function() {
				if (this && typeof this == 'string') {
					display_value = this;
					return false;
				}
			});
		}

		display_value = display_value || '[unnamed]';

		$('<h3/>')
			.text(display_value)
			.appendTo(self.node);

		$('<a/>')
			.addClass('button')
			.text('Details')
			.click(function() { $(obj.ui_details().node).appendTo(self.node); })
			.appendTo(self.node);

		$('<a/>')
			.addClass('button')
			.text('Modify')
			.click(function() { $(obj.ui_edit().node).appendTo(self.node); })
			.appendTo(self.node);

		$('<a/>')
			.addClass('button')
			.text('Delete')
			.click(function() {
				if (confirm('Are you sure you want to delete this object?')) {
					model.del(obj.id, function(data) {
						alert('Successfully deleted');
						self.node.slideUp();
					});
				}
			})
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
		this.label = $('<label/>').html(properties._label || properties.name.replace(/^(.)/g, String.toUpperCase) || '&nbsp;');
		this.field = $('<' + (properties._tagName || 'input') + '/>');
		this.text = $('<span/>');
		this.fields = [this.field];

		properties.id = properties.id || 'field_' + properties.name;
		properties.id += Math.round(Math.random() * 99999);

		this.add_choices = function(choices) {
			for (var i in choices) {
				choices[i].text = choices[i].text || choices[i].value;
				var opt = $('<option/>').attr(choices[i]);

				this.field.append(opt)
			}
		}

		this.add_field = function() {
			var field = this.field.clone()
				.css('display', 'block')
				.val('')
				.insertAfter(this.fields[this.fields.length - 1])
				.focus()

			this.fields.push(field);

			return field;
		}

		for (var p in properties) {
			var v = properties[p];

			if (p.indexOf('_') == 0)
				continue;

			switch (p) {
				case 'choices':
					this.add_choices(v);
					break;
				default:
					this.field.attr(p, v);
			}
		}

		/**
		 * Switches from an input field to a text value display
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

		if (properties.value) {
			if ($.isArray(properties.value)) {
				this.field.val(properties.value.shift());
				$(properties.value).each(function() {
					self.add_field().val(this);
				});
			}
			else
				this.field.val(properties.value);
		}

		this.text.html(this.field.val() || '&nbsp;');
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	textarea: function(properties) {
		properties._tagName = 'textarea';
		properties.innerHTML = properties.value;
		properties.rows = properties.rows || 3;
		properties.cols = properties.cols || 48;
		boto_web.ui._field.call(this, properties);
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	text: function(properties) {
		properties.size = properties.size || 50;
		var self = this;

		if (properties._type == 'password')
			properties.type = 'password';

		boto_web.ui._field.call(this, properties);

		if (properties._type == 'password') {
			this.field.val('');
			this.text.text('******');
		}

		if (properties._type == 'list') {
			$('<div/>')
				.text('Add another value')
				.addClass('add button')
				.click(function() { self.add_field() })
				.appendTo(self.field_container)
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
		var self = this;

		this.datepicker = $(this.field).datepicker({
			showOn: 'both',
			dateFormat: 'yy-mm-dd',
			altField: this.field,
			changeMonth: true,
			changeYear: true,
			constrainInput: false
		});
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	picklist: function(properties, data) {
		properties._tagName = 'select';
		properties.choices = [];

		boto_web.ui._field.call(this, properties);

		var self = this;

		if (properties._type == 'list') {
			this.field.attr({cols: 5, multiple: 'multiple'});
		}

		if (properties._label in boto_web.env.models) {
			boto_web.env.models[properties._label].all(function(data) {
				var value_text = '';

				try {
					self.add_choices($(data).map(function() {
						if (this.id == properties.value)
							value_text = this.properties.name;

						return { text: this.properties.name, value: this.id };
					}));
				} catch (e) { }

				self.field.val(properties.value);
				self.text.text(value_text);
			});
		}
	}
};

boto_web.ModelMeta.prototype.ui_create = function(opts) { return new boto_web.ui.BaseModelEditor(this, undefined, opts); };

boto_web.Model.prototype.ui_edit = function(opts) { return new boto_web.ui.BaseModelEditor(boto_web.env.models[this.name], this, opts); };

boto_web.Model.prototype.ui_display = function(opts) { return new boto_web.ui.BaseModelDisplay(boto_web.env.models[this.name], this, opts); };
boto_web.Model.prototype.ui_details = function(opts) {
	if (!opts)
		opts = {};

	opts.read_only = true;

	return new boto_web.ui.BaseModelEditor(boto_web.env.models[this.name], this, opts);
};