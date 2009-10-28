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
		'search':         '*[bwWidget=search]',
		'search_results': '*[bwWidget=searchResults]',
		'breadcrumbs':    '*[bwWidget=breadcrumbs]',
		'attribute_list': '*[bwWidget=attributeList]',
		'editing_tools':  '*[bwWidget=editingTools]',
		'attribute':      '*[bwAttribute]',
		'link':           'a[bwLink]'
	},

	properties: {
		'model':          'bwModel',
		'link':           'bwLink',
		'attribute':      'bwAttribute',
		'attributes':     'bwAttributes',
		'def':        'bwDefault'
	},

	handlers: {
		'edit': function(action) {
			var obj = action.split('/');
			boto_web.env.models[obj[1]].get(obj[2], function(obj) {
				obj.edit();
			});
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

		new boto_web.ui.Object($('header'), env.models.User, {properties: env.user});

		$('header nav li').addClass('ui-state-default ui-corner-top');
		$('header nav').show();

		if (document.location.hash == '')
			document.location.href = $('header nav ul a:first').attr('href');

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
		self.obj = obj;
		self.model = model;
		self.fields = [];

		$(self.properties).each(function() {
			var props = this;

			if (typeof obj != 'undefined')
				props = $.extend(this, {value: obj.properties[this.name]});

			if (props._perm && $.inArray('write', props._perm) == -1)
				return;

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
				case 'blob':
					field = new boto_web.ui.file(props)
						.read_only(opts.read_only);
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
					boto_web.ui.alert('The database has been updated.');
				}
				else {
					boto_web.ui.alert('There was an error updating the database.');
				}
				// TODO data save callback
			});
		};

		$('<br/>')
			.addClass('clear')
			.appendTo(self.node);

		var closeFcn = function() { $(this).dialog("close"); document.location.href = document.location.href.replace(/&?action=(edit|create)\/[^&]*/, '') };
		$(self.node).dialog({
			modal: true,
			title: model.name + ' Editor',
			width: 500,
			buttons: {
				Save: function() { self.submit(); closeFcn.call(this); },
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

		var closeFcn = function() { $(this).dialog("close"); document.location.href = document.location.href.replace(/&?action=delete\/[^&]*/, '') };
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


	/**
	 * Generic interface for all field types.
	 *
	 * @param {Object} properties HTML node properties.
	 */
	_field: function(properties) {
		var self = this;
		this.node = $('<div/>');
		this.label = $('<label/>').html(properties._label || properties.name.replace(/^(.)/g, function(a,b) { return b.toUpperCase() }) || '&nbsp;');
		this.field = $('<' + (properties._tagName || 'input') + '/>');
		this.text = $('<span/>');
		this.fields = [this.field];
		this.perms = properties._perms || [];

		properties.id = properties.id || 'field_' + properties.name;
		properties.id += Math.round(Math.random() * 99999);

		this.add_choices = function(choices) {
			if (this.field.children().length == 0)
				$('<option/>').appendTo(this.field);

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
	file: function(properties) {
		properties._type = 'file';
		boto_web.ui._field.call(this, properties);
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
	},

	action_handler: function(params) {
		if (!params.action) return;

		$(params.action).each(function() {
			if (boto_web.ui.handlers[this.replace(/\/.*/,'')])
				boto_web.ui.handlers[this.replace(/\/.*/,'')](this);
		});
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
				for (var sel in boto_web.env.opts.markup) {
					data.find(sel).each(boto_web.env.opts.markup[sel]);
				}
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