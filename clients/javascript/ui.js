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
	sections: [],

	widgets: {},

	selectors: {
		'section':        'section',
		'object':         'article, .bwObject',
		'header':         'header',
		'details':        'fieldset.details',
		'widget':         '*[bwWidget]',
		'relations':      '*[bwWidget=relations]',
		'report':         '*[bwWidget=report]',
		'search':         '*[bwWidget=search]',
		'search_results': '*[bwWidget=searchResults]',
		'breadcrumbs':    '*[bwWidget=breadcrumbs]',
		'attribute_list': '*[bwWidget=attributeList]',
		'editing_tools':  '*[bwWidget=editingTools]',
		'date_time':      '*[bwWidget=dateTime]',
		'model':          '*[bwModel]',
		'condition':      '*[bwCondition]',
		'attribute':      '*[bwAttribute]',
		'template':       '*[bwTemplate]',
		'class_name':     '*[bwClass]',
		'link':           'a[bwLink]'
	},

	properties: {
		'model':          'bwModel',
		'link':           'bwLink',
		'attribute':      'bwAttribute',
		'attributes':     'bwAttributes',
		'condition':      'bwCondition',
		'template':       'bwTemplate',
		'class_name':     'bwClass',
		'def':            'bwDefault'
	},

	handlers: {
		'edit': function(action) {
			var obj = action.split('/');
			boto_web.env.models[obj[1]].get(obj[2], function(obj) {
				obj.edit();
			});
		},
		'update': function(action, params) {
			var data;
			var obj = action.split('/');
			eval('data = ' + unescape(params.data));
			data.id = obj[2];
			boto_web.env.models[obj[1]].save(data, function() {
				boto_web.ui.alert('The database has been updated.');
			});
			var href = '' + document.location.href;
			document.location.href = href.replace(/(&|\?)action=update[^&]*&data=[^&]*/, '');
		},
		'delete': function(action) {
			var obj = action.split('/');
			boto_web.env.models[obj[1]].get(obj[2], function(obj) {
				obj.del();
			});
		},
		'create': function(action) {
			var model = action.split('/');
			boto_web.env.models[model[1]].create();
		}
	},

	/**
	 * Initializes the boto_web interface.
	 *
	 * @param {boto_web.Environment} env The current boto_web environment.
	 */
	init: function(env) {
		var self = boto_web.ui;

		if (self.use_default) {
			self.default_ui(env);
			return;
		}

		self.desktop = new boto_web.ui.Desktop();

		if (env.opts.handlers)
			self.handlers = $.extend(self.handlers, env.opts.handlers);

		new boto_web.ui.Object($('header'), env.models.User, {id: env.user.id, properties: env.user});
		var frame = new boto_web.ui.Page($('<section/>'));
		frame.node = $('body');
		frame.parse_markup();

		$('header nav li').addClass('ui-state-default ui-corner-top');
		$('header nav').show();

		if (document.location.hash == '')
			document.location.href = $('header nav ul a:first').attr('href');

		if ($('#global_search')) {
			$('#global_search input')
				.keyup(function(e) {
					if (e.keyCode == 13) {
						document.location.href = $('#global_search').attr('action') + '?q=' + this.value;
						this.value = '';
					}
				})
		}

		$('<iframe name="server" class="hidden"/>').appendTo('body');

		boto_web.ui.watch_url();
	},

	default_ui: function(env) {
		var self = boto_web.ui;

		// Merge homepage as a generated false model
		$.each($.merge([{obj: {href: 'home', name: 'Home', home: 1}}], env.routes), function() {
			var model = this.obj;

			if (typeof this.obj == 'string')
				model = env.models[this.obj];

			model.section = new boto_web.ui.Section(model, env);
			$('<a/>')
				.attr({href: '#' + this.href})
				.text(model.name)
				.appendTo($('<li/>').appendTo(self.nav));

			self.sections[model.href] = model.section;
		});
	},

	add_section: function(data) {
		if (data.model)
			model = env.models[data.model];

		model.section = new boto_web.ui.Section(model, env);
		$('<a/>')
			.attr({href: '#' + this.href})
			.text(model.name)
			.appendTo($('<li/>').appendTo(self.nav));

		self.sections[model.href] = model.section;
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

	decorate: function(node) {
		node.find('.ui-state-default')
			.hover(function() {
				$(this).addClass('ui-state-hover')
			},
			function() {
				$(this).removeClass('ui-state-hover')
			})
	},

	alert: function(msg) {
		$('<div/>')
			.html(msg)
			.dialog({
				modal: true,
				dialogClass: 'alert',
				buttons: {
					Ok: function() { $(this).dialog('close'); }
				}
			})
			.dialog('show')
	},

	BaseModelEditor: function(model, obj, opts) {
		var self = this;

		if (!opts)
			opts = {};

		opts = $.extend({read_only: false}, opts);

		self.node = $('<div/>')
			.addClass('editor')
			.addClass(model.name);

		self.properties = model.properties;
		self.num_properties = $.grep(self.properties, function(o) { return $.inArray('write', o._perm) }).length;
		self.obj = obj;
		self.opts = opts;
		self.model = model;
		self.fields = [];

		if (self.num_properties > 20) {
			self.per_column = Math.ceil(self.num_properties / 3);
			self.columns = [
				$('<div/>')
					.addClass('al p33')
					.appendTo(self.node),
				$('<div/>')
					.addClass('al p33')
					.appendTo(self.node),
				$('<div/>')
					.addClass('al p33')
					.appendTo(self.node)
			]
		}
		else if (self.num_properties > 10) {
			self.per_column = Math.ceil(self.num_properties / 2);
			self.columns = [
				$('<div/>')
					.addClass('al p50')
					.appendTo(self.node),
				$('<div/>')
					.addClass('al p50')
					.appendTo(self.node)
			]
		}
		else {
			self.per_column = self.num_properties + 1;
			self.columns = [self.node];
		}

		$(self.properties).each(function(num, props) {
			if ('def' in opts)
				props = $.extend(props, {value: opts.def[props.name]});

			if (typeof obj != 'undefined')
				props = $.extend(props, {value: obj.properties[props.name]});

			if (props._perm && $.inArray('write', props._perm) == -1)
				return;

			// TODO Generalize complexType options
			if (props._type == 'complexType') {
				if (!self.obj) {
					return;
				}
				opts.choices = [{text: 'ID', value: 'id'}];
				if (self.obj.properties.primary_key && self.obj.properties.primary_key != 'id')
					opts.choices.push({text: self.obj.properties.primary_key, value: self.obj.properties.primary_key});

				$(boto_web.env.models[self.obj.properties.target_class_name].properties).each(function() {
					if ($.inArray('write', this._perm) >= 0)
						opts.choices.push({text: this._label, value: this.name});
				});
				opts.choices.sort(function(a,b) { return (a.text.toLowerCase() > b.text.toLowerCase()) ? 1 : -1; });
			}

			var field = boto_web.ui.property_field(props, opts);

			if (typeof field == 'undefined') return;

			self.fields.push(field);
			field.node.addClass(num % 2 ? 'even' : 'odd');
			field.node.appendTo(self.columns[Math.floor(num / self.per_column)]);
		});

		self.submit = function(closeFcn) {
			var self = this;
			var data = {};
			var uploads = [];

			if (self.obj)
				data.id = self.obj.id;

			$(self.fields).each(function() {
				var val;
				var name = this.field.attr('name');

				if (this.field.attr('type') == 'file') {
					uploads.push(this);
					return;
				}

				val = this.field_container.data('get_value')()

				if (typeof val == 'undefined')
					return;

				if (!self.obj || !$.equals((self.obj.properties[name] || ''), val))
					data[name] = val;
			});

			self.model.save(data, function(data) {
				if (data.status < 300) {
					if (uploads.length) {
						var upload_fnc = function(obj) {
							$(uploads).each(function() {
								if ($(this.field).val())
									$(this.field).parent('form').attr('action', boto_web.env.base_url + obj.href + '/' + obj.id + '/' + this.field.attr('name')).submit();

								closeFcn.call(self.node);

								boto_web.ui.alert('The database has been updated.');

								if (opts.callback) {
									opts.callback();
								}
								//$(this.field).uploadifySettings('script', boto_web.env.base_url + obj.href + '/' + obj.id + '/' + this.field.attr('name'));
								/*$(this.field).uploadifySettings('onComplete', function() {
									closeFcn();
									boto_web.ui.alert('The database has been updated.');
								});*/
								//$(this.field).uploadifyUpload();
							});
						};

						if (self.obj)
							upload_fnc(self.obj);
						else
							self.model.get(data.getResponseHeader('Location'), upload_fnc);
					}
					else
						boto_web.ui.alert('The database has been updated.');

					if (opts.callback) {
						opts.callback();
					}
				}
				else {
					boto_web.ui.alert('There was an error updating the database:<br />' + data.responseText);
				}
				// TODO data save callback
			});

			if (uploads.length)
				return false;
			return true;
		};

		$('<br/>')
			.addClass('clear')
			.appendTo(self.node);

		var closeFcn = function() { $(this).dialog("destroy"); $(this).empty(); document.location.href = document.location.href.replace(/&?action=(edit|create)\/[^&]*/, '') };
		$(self.node).dialog({
			modal: true,
			title: model.name + ' Editor',
			width: 300 * self.columns.length,
			buttons: {
				Save: function() { if (self.submit(closeFcn)) closeFcn.call(this); },
				Cancel: closeFcn
			}
		});

		$(self.node).dialog('show');
	},

	BaseModelDeletor: function(model, obj, opts) {
		var self = this;

		self.model = model;
		self.obj = obj;

		if (!opts)
			opts = {};

		self.node = $('<div/>')
			.text('Do you want to delete this ' + model.name + '?')
			.addClass('deletor')
			.addClass(model.name);

		self.submit = function() {
			self.model.del(self.obj.id, function(data) {
				if (data.status < 300) {
					boto_web.ui.alert('The database has been updated.');
				}
				else {
					boto_web.ui.alert('There was an error updating the database.');
				}
				// TODO data save callback
			});
		};

		var closeFcn = function() { $(this).dialog("destroy"); $(this).empty(); document.location.href = document.location.href.replace(/&?action=delete\/[^&]*/, '') };
		$(self.node).dialog({
			modal: true,
			title: 'Please confirm',
			dialogClass: 'confirm',
			buttons: {
				'Yes, delete it': function() { self.submit(); closeFcn.call(this); },
				Cancel: closeFcn
			}
		});

		$(self.node).dialog('show');
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


	property_field: function(props, opts) {
		if (!opts) opts = {read_only: false};
		switch ((props._type == 'list') ? (props._item_type) : props._type) {
			case 'string':
			case 'str':
			case 'integer':
			case 'password':
				if (props.choices)
					return new boto_web.ui.dropdown(props)
						.read_only(opts.read_only);
				else if (props.maxlength > 1024)
					return new boto_web.ui.textarea(props)
						.read_only(opts.read_only);
				else
					return new boto_web.ui.text(props)
						.read_only(opts.read_only);
			case 'dateTime':
				return new boto_web.ui.date(props)
					.read_only(opts.read_only);
			case 'boolean':
				return new boto_web.ui.bool(props)
					.read_only(opts.read_only);
			case 'complexType':
				return new boto_web.ui.complex(props, opts.choices)
					.read_only(opts.read_only);
			case 'blob':
				return new boto_web.ui.file(props)
					.read_only(opts.read_only);
			default:
				return new boto_web.ui.picklist(props)
					.read_only(opts.read_only);
		}
	},


	/**
	 * Generic interface for all field types.
	 *
	 * @param {Object} properties HTML node properties.
	 */
	_field: function(properties) {
		var self = this;
		this.node = $('<dl/>');
		this.label = $('<dt/>').html(properties._label || properties.name.replace(/^(.)/g, function(a,b) { return b.toUpperCase() }) || '&nbsp;');
		this.field = $('<' + (properties._tagName || 'input') + '/>');
		this.text = $('<span/>');
		this.fields = [this.field];
		this.perms = properties._perms || [];
		this.properties = properties;

		properties.id = properties.id || 'field_' + properties.name;
		properties.id += Math.round(Math.random() * 99999);

		this.add_choices = function(choices) {
			if (!this.has_options) {
				this.has_options = true;
				$('<option/>').appendTo(this.field);
			}

			for (var i in choices) {
				choices[i].text = choices[i].text || choices[i].value;
				var opt = $('<option/>').attr(choices[i]);

				this.field.append(opt)
			}
		}

		this.add_field = function(value) {
			var field = this.field.clone()
				.attr('id', this.field.attr('id') + '_' + this.fields.length)
				.val(value || '')
				.insertAfter($('<br />').insertAfter(this.fields[this.fields.length - 1]))
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

		this.field_container = $('<dd/>').addClass('field_container').append(this.field);
		this.node.append(this.label, this.field_container, this.text);
		this.read_only();

		this.field_container.data('get_value', function() {
			if (self.fields.length > 1) {
				var val = [];
				$(self.fields).each(function() {
					val.push(this.val());
				});
				return val;
			}
			return self.field.val();
		});

		if ($.isArray(properties.value)) {
			$(properties.value).each(function(i ,prop) {
				if (i == 0)
					self.field.val(prop);
				else
					self.add_field(prop);
			});
		}
		else
			this.field.val(properties.value || '');

		this.text.html(this.field.val() || '&nbsp;');

		$('<br/>')
			.addClass('clear')
			.appendTo(self.field_container);

		if (properties._type == 'list') {
			$('<span/>')
				.html('<span class="ui-icon ui-icon-triangle-1-s"></span>Add another value')
				.addClass('ui-button ui-state-default ui-corner-all')
				.click(function(e) { self.add_field(); e.preventDefault(); })
				.appendTo(self.field_container);
		}

		if (properties._item_type in boto_web.env.models) {
			$('<span/>')
				.html('<span class="ui-icon ui-icon-plusthick"></span>New ' + properties._item_type)
				.addClass('ui-button ui-state-default ui-corner-all')
				.click(function(e) { boto_web.env.models[properties._item_type].create({callback: function() {self.init()}}); e.preventDefault(); })
				.appendTo(self.field_container);
		}

		$('<br/>')
			.addClass('clear')
			.appendTo(self.field_container);
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
	bool: function(properties) {
		properties.type = 'radio';
		boto_web.ui._field.call(this, properties);

		var no_field = this.add_field();
		var self = this;

		this.field_container.find('br').remove();

		this.field.value = '1';
		no_field.value = '0';

		if (properties.value == 'True')
			this.field.attr('checked', true);
		else
			no_field.attr('checked', true);

		$('<label/>')
			.css('display', 'inline')
			.html(' Yes &nbsp; &nbsp; ')
			.attr({htmlFor: this.field.attr('id')})
			.insertAfter(this.field);

		$('<label/>')
			.css('display', 'inline')
			.html(' No')
			.attr({htmlFor: no_field.attr('id')})
			.insertAfter(no_field);

		self.field_container.data('get_value', function() {
			return self.field.is(':checked') ? 'True' : 'False';
		});
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	complex: function(properties, choices) {
		boto_web.ui._field.call(this, properties);

		var self = this;

		this.field_container.empty();

		$(properties.value).each(function() {
			$('<dl/>')
				.addClass('mapping')
				.append(
					$('<dt/>')
						.text(this.name),
					$('<dd/>').append(
						//$('<input/>')
						//	.text(this.name)
						new boto_web.ui.dropdown({name: this.name, choices: choices}).field.val(this.value)
					)
				)
				.appendTo(self.field_container);
		});

		self.field_container.data('get_value', function() {
			var value = [];
			$(self.field_container).find('.mapping').each(function() {
				value.push({
					name: $(this).find('dt').text(),
					value: $(this).find('input, select').val(),
					type: 'string'
				});
			});
			return value;
		});
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	text: function(properties) {
		var self = this;

		if (properties._type == 'password')
			properties.type = 'password';

		boto_web.ui._field.call(this, properties);

		if (properties._type == 'password') {
			this.field.val('');
			$('<br/>').appendTo(this.field_container);
			this.reset = $('<input/>')
				.attr({ type: 'checkbox', id: this.field.id + '_reset' })
				.appendTo(this.field_container);
			$('<label/>')
				.css('display', 'inline')
				.attr({'htmlFor': this.reset.id})
				.text(' Send password reset email')
				.appendTo(this.field_container);
			this.text.text('******');

			self.field_container.data('get_value', function() {
				if (self.reset.is(':checked'))
					return '';
				else if (self.field.val() == '')
					return;
				else
					return self.field.val();
			});
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
			showOn: 'button',
			duration: '',
			dateFormat: 'yy-mm-dd',
			showTime: true,
			time24h: true,
			altField: this.field,
			changeMonth: true,
			changeYear: true,
			constrainInput: false,
			onClose: function(dateText, inst) {
				dateText = dateText.replace(' GMT', '') + ' GMT';
				this.value = dateText;
			}
		});

		this.field.val(this.field.val().replace('T', ' ').replace(/(\d+:\d+)(:\d+)?Z?.*/, '$1 GMT'));

		$('<div/>')
			.addClass('small')
			.text('format: yyyy-mm-dd hh:mm:ss GMT')
			.appendTo(this.field_container);

		self.field_container.data('get_value', function() {
			return self.field.val().replace(/(\d+-\d+-\d+) (\d+:\d+).*/,'$1T$2:00Z');
		});
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	file: function(properties) {
		properties.type = 'file';
		boto_web.ui._field.call(this, properties);

		var self = this;

		$('<form/>')
			.attr({method: 'post', enctype: 'multipart/form-data', target: 'server'})
			.append(self.field.remove())
			.appendTo(self.field_container);

/*		setTimeout(function() {
			$(self.field).uploadify({
				uploader: 'swf/uploadify.swf',
				cancelImg: 'images/cancel.png',
				auto: false,
				method: 'POST',
				buttonText: 'Choose File'
			});
		}, 50);*/
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	picklist: function(properties) {
		properties._tagName = 'select';
		properties.choices = [];

		boto_web.ui._field.call(this, properties);

		var self = this;

		self.init = function() {
			if (!(self.properties._item_type in boto_web.env.models))
				return;

			self.model = boto_web.env.models[self.properties._item_type];
			/*
			 * The following code was used to display a dropdown instead of a search
			 * field when choosing objects.
			self.model.count(function(count) {
				if (count < 0) {
					self.field.empty();

					self.model.all(function(data, page) {
						var value_text = '';

						try {
							self.add_choices($(data).map(function() {
								if (this.id == self.properties.value)
									value_text = this.properties.name;

								return { text: this.properties.name, value: this.id };
							}));
						} catch (e) { }

						if (self.properties.value)
							self.field.val(self.properties.value.id);
						self.text.text(value_text);

						return page < 10;
					});
				}
				else {
			*/
					self.has_search = true;
					self.field_container.empty();

					$('<span/>')
						.addClass('ui-icon ui-icon-search')
						.appendTo(self.field_container);

					var add_selection = function(id, name) {
						$('<div/>')
							.addClass('clear')
							.attr('id', 'selection_' + id)
							.html('<span class="ui-icon ui-icon-closethick" onclick="$(this).parent().remove()"></span> ' + name)
							.appendTo(self.field_container.find('.selections'))
					}

					$('<input/>')
						.addClass('search_field')
						.keyup(function(e) {
							if (e.keyCode != 13) return;

							var node = $(this);
							var val = node.val();
							node.siblings('.search_results').empty();
							self.model.query([
								//TODO enable searching by id
								//['id', '=', val],
								['name', 'like', '%' + val + '%']
							], function(obj, page) {
								for (var i in obj) {
									$('<a/>')
										.css('display', 'block')
										.attr({id: 'search_option_' + obj[i].id, href: '#'})
										.text(obj[i].properties.name)
										.click(function(e){
											if (self.properties._type != 'list')
												node.siblings('.selections').empty();

											add_selection($(this).attr('id').replace('search_option_',''), $(this).html());
											e.preventDefault();
										})
										.appendTo(node.siblings('.search_results'))
								}
								return page < 10;
							});
						})
						.appendTo(self.field_container);

					$('<div/>')
						.addClass('search_results')
						.appendTo(self.field_container);

					$('<strong/>')
						.text('Your selection' + ((self.properties._type == 'list') ? 's' : '') + ':')
						.appendTo(self.field_container);
					$('<div/>')
						.addClass('selections')
						.appendTo(self.field_container);

					$('<span/>')
						.html('<span class="ui-icon ui-icon-plusthick"></span>New ' + self.properties._item_type)
						.addClass('ui-button ui-state-default ui-corner-all')
						.click(function(e) { boto_web.env.models[self.properties._item_type].create(); e.preventDefault(); })
						.appendTo(self.field_container);

					$('<br/>')
						.addClass('clear')
						.appendTo(self.field_container);

					if (self.properties.value) {
						if (!$.isArray(self.properties.value))
							self.properties.value = [self.properties.value];

						$(self.properties.value).each(function() {
							self.model.get(this.id || this, function(obj) {
								add_selection(obj.id, obj.properties.name);
							});
						});
					}

					self.field_container.data('get_value', function() {
						var val = [];

						self.field_container.find('.selections div').each(function() {
							val.push(this.id.replace('selection_', ''));
						});

						if (val.length == 1)
							val = val[0];
						if (val.length == 0)
							val = '';

						return val;
					});
			/*	}
			});
			*/
		}

		self.init();
	},

	action_handler: function(params) {
		if (!params.action) return;

		$(params.action).each(function() {
			if (boto_web.ui.handlers[this.replace(/\/.*/,'')])
				boto_web.ui.handlers[this.replace(/\/.*/,'')](this, params);
		});
	},

	sort_props: function(a,b) {
		return (a._label || a.name || a).toLowerCase() > (b._label || b.name || b).toLowerCase() ? 1 : -1;
	}
};

boto_web.ModelMeta.prototype.create = function(opts) { return new boto_web.ui.BaseModelEditor(this, undefined, opts); };

boto_web.Model.prototype.edit = function(opts) { return new boto_web.ui.BaseModelEditor(boto_web.env.models[this.name], this, opts); };
boto_web.Model.prototype.del = function(opts) { return new boto_web.ui.BaseModelDeletor(boto_web.env.models[this.name], this, opts); };

// location binding system taken from:
// http://www.bennadel.com/blog/1520-Binding-Events-To-Non-DOM-Objects-With-jQuery.htm
// Our plugin will be defined within an immediately
// executed method.
boto_web.ui.watch_url = function() {
	// Default to the current location.
	var strLocation = window.location.href;
	var strHash = window.location.hash;
	var strPrevLocation = "";
	var strPrevHash = "";

	// This is how often we will be checkint for
	// changes on the location.
	var intIntervalTime = 100;

	// This method removes the pound from the hash.
	var fnCleanHash = function( strHash ){
		return(
			strHash.substring( 1, strHash.length )
			);
	}

	// This will be the method that we use to check
	// changes in the window location.
	var fnCheckLocation = function(){
		// Check to see if the location has changed.
		if (strLocation != strPrevLocation){

			// Store the new and previous locations.
			strPrevLocation = strLocation;
			strPrevHash = strHash;
			strLocation = window.location.href;
			strHash = window.location.hash;

			// The location has changed. Trigger a
			// change event on the location object,
			// passing in the current and previous
			// location values.
			$( window.location ).trigger(
				"change",
				{
					currentHref: strLocation,
					currentHash: fnCleanHash( strHash ),
					previousHref: strPrevLocation,
					previousHash: fnCleanHash( strPrevHash )
				}
			);

		}
	}

	// Set an interval to check the location changes.
	setInterval( fnCheckLocation, intIntervalTime );

	$(window.location).bind(
		"change",
		function(objEvent, objData) {
			var static_url = objData.currentHash.replace(/#|\?(.*)/g, '');

			if (RegExp.$1) {
				boto_web.ui.params = {};
				$(RegExp.$1.split('&')).each(function() {
					var pair = this.split('=');
					if (boto_web.ui.params[pair[0]])
						boto_web.ui.params[pair[0]].push(pair[1]);
					else
						boto_web.ui.params[pair[0]] = [pair[1]];
				});

				boto_web.ui.action_handler(boto_web.ui.params);
			}

			if (boto_web.ui.current_url != static_url)
				boto_web.ui.current_url = static_url;
			else
				return;

			$.get(static_url, null, function(data) {
				data = $(data);
				new boto_web.ui.Page(data).activate();
			});
		}
	);
}

jQuery.fn.log = function (msg) {
	console.log("%s: %o", msg, this);
	return this;
};
/*
$.extend(jQuery.jStore.defaults, {
	project: 'newscore'
})
*/

$.equals = function(o, compareTo) {
	if (typeof o != typeof compareTo)
		return false;

	if ($.isArray(o)) {
		if (o.length != compareTo.length)
			return false;

		for (var i=0; i<o.length; i++) {
			if (!$.equals(o[i], compareTo[i]))
				return false;
		}

		return true;
	}
	else if (typeof o == 'object') {
		for (var i in o) {
			if (!(i in compareTo) || o[i] !== compareTo[i]) {
				return false;
			}
		}
		for (var i in compareTo) {
			if (!(i in o) || o[i] !== compareTo[i]) {
				return false;
			}
		}
		return true;
	}

	return o === compareTo;
}
