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
		'trigger':        '*[bwTrigger]',
		'editable':       '*[bwEditable]',
		'attribute':      '*[bwAttribute]',
		'template':       '*[bwTemplate]',
		'class_name':     '*[bwClass]',
		'existing_only':  '*[bwExistingOnly]',
		'link':           'a[bwLink]'
	},

	properties: {
		'model':          'bwModel',
		'link':           'bwLink',
		'attribute':      'bwAttribute',
		'attributes':     'bwAttributes',
		'condition':      'bwCondition',
		'trigger':        'bwTrigger',
		'template':       'bwTemplate',
		'editable':       'bwEditable',
		'class_name':     'bwClass',
		'filter':         'bwFilter',
		'existing_only':  'bwExistingOnly',
		'def':            'bwDefault',
		'widget':         'bwWidget'
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

	alert: function(msg, title, callback) {
		$('<div/>')
			.html(msg)
			.dialog({
				modal: true,
				dialogClass: 'alert',
				title: title || 'Alert',
				buttons: {
					Ok: function() { $(this).dialog('close'); if (callback) callback(); }
				}
			})
			.dialog('show')
	},

	BaseModelEditor: function(model, obj, opts) {
		var self = this;

		if (!opts)
			opts = {};

		opts = $.extend({read_only: false, hide: []}, opts);

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
			if ('def' in opts && props.name in opts.def) {
				props = $.extend(props, {value: opts.def[props.name]});
				opts.hide.push(props.name);
			}

			if (typeof obj != 'undefined')
				props = $.extend(props, {value: obj.properties[props.name]});
			else
				opts.allow_default = true;

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

				if (self.obj.properties.target_class_name) {
					$(boto_web.env.models[self.obj.properties.target_class_name].properties).each(function() {
						if ($.inArray('write', this._perm) >= 0)
							opts.choices.push({text: this._label, value: this.name});
					});
					opts.choices.sort(function(a,b) { return (a.text.toLowerCase() > b.text.toLowerCase()) ? 1 : -1; });
				}
			}

			var field = boto_web.ui.forms.property_field(props, opts);

			if (typeof field == 'undefined') return;

			self.fields.push(field);

			if ($.inArray(props.name, opts.hide) < 0) {
				field.node.addClass(num % 2 ? 'even' : 'odd');
				field.node.appendTo(self.columns[Math.floor(num / self.per_column)]);
			}
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

				if (val != '' && !self.obj || self.obj && !$.equals((self.obj.properties[name] || ''), val))
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

								//document.location.reload(true);
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
					else {
						closeFcn.call(self.node);
						boto_web.ui.alert('The database has been updated.');
						document.location.reload(true);
					}

					if (opts.callback) {
						opts.callback();
					}
				}
				else {
					self.save_button.removeClass('ui-state-disabled');
					self.submitting = false;
					boto_web.ui.alert($(data.responseXML).find('message').text(), 'There was an error updating the database');
				}
				// TODO data save callback
			});

			if (uploads.length)
				return false;
			return false;
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
				Save: function() {
					if (self.submitting)
						return;
					// Disable clicking Save again
					self.save_button = $(this).siblings('.ui-dialog-buttonpane').find('button:eq(0)');
					self.save_button.addClass('ui-state-disabled');
					self.submitting = true;

					if (self.submit(closeFcn))
						closeFcn.call(this);
				},
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

					var safety = 0;

					// Go back until we hit a page that doesn't belong to this object.
					while (document.location.hash.indexOf('id=' + self.obj.id) >= 0 && safety++ < 20) {
						history.go(-1);
					}

					document.location.reload(true);
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

			if (!static_url) return;

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
	try {
		console.log("%s: %o", msg, this);
	} catch(e) {}
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

$('body').ajaxStop(function(){
	$('.dataTables_wrapper table').each(function() {
		var table = $(this).data('data_table');

		if (table) {
			table.stop();
			table.data_table.fnDraw();
		}
	});
});