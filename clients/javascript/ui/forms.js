/**
 * @projectDescription Provides standard form fields for use in botoweb.
 *
 * @author    Ian Paterson
 * @namespace boto_web.ui.forms
 */

/**
 * Enhanced form elements capable of representing and allowing input to the
 * various botoweb data types.
 */
boto_web.ui.forms = {
	property_field: function(props, opts) {
		var self = this;

		if (!props || !props.name) return;

		switch ((props._type == 'list') ? (props._item_type) : props._type) {
			case 'string':
			case 'str':
			case 'integer':
				if (props.choices)
					return new self.dropdown(props, opts);
				else if (props.maxlength > 1024)
					return new self.textarea(props, opts);
				else
					return new self.text(props, opts);
			case 'text':
				return new self.textarea(props, opts);
			case 'password':
				return new self.password(props, opts);
			case 'dateTime':
				return new self.date(props, opts);
			case 'boolean':
				return new self.bool(props, opts);
			case 'complexType':
				return new self.complex(props, opts);
			case 'blob':
				return new self.file(props, opts);
			default:
				return new self.picklist(props, opts);
		}
	},


	/**
	 * Generic interface for all field types.
	 *
	 * @param {Object} properties HTML node properties.
	 */
	_field: function(properties, opts) {
		var self = this;
		this.opts = opts || {read_only: false};
		this.node = this.opts.node || $('<dl/>');
		this.label = $('<dt/>').html(properties._label || properties.name.replace(/^(.)/g, function(a,b) { return b.toUpperCase() }) || '&nbsp;');
		this.field = $('<' + (properties._tagName || 'input') + '/>');
		this.text = $('<span/>');
		this.fields = [this.field];
		this.perms = properties._perms || [];
		this.properties = properties;
		this.editing_template = this.opts.editing_template;
		this.nested_objs = [];
		this.existing_only = this.opts.existing_only;

		if (this.existing_only)
			this.editing_template = '';

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
			var field;

			if (this.editing_template) {
				if (this.properties._type != 'list' && this.fields.length >= 2)
					return;

				field = this.editing_template.clone(value);
				this.nested_objs.push(field);
				field.edit(true);
				$(field.node).show();

				self.field_container.append(
					$('<br />'),
					field.node
				);
			}
			else {
				// Unescape HTML entities
				if (value)
					value = $('<div/>').html(value || '').text();

				field = this.field.clone()
					.attr('id', this.field.attr('id') + '_' + this.fields.length)
					.val(value || '')
					.insertAfter($('<br />').appendTo(this.field_container))
					.focus()
			}

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

		var container_tag = (this.opts.node) ? 'div' : 'dd';

		this.field_container = $('<' + container_tag + '/>').addClass('field_container').append(this.field);

		if (!this.opts.no_label)
			this.node.append(this.label);

		this.node.append(this.field_container);

		if (!this.opts.no_text)
			this.node.append(this.text);

		this.read_only(this.opts.read_only);

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

		if (this.opts.allow_default && (!properties.value || properties.value.length == 0))
			properties.value = properties._default_value || '';

		if ($.isArray(properties.value)) {
			$(properties.value).each(function(i ,prop) {
				if (i == 0)
					self.field.val($('<div/>').html(prop || '').text());
				else
					self.add_field(prop);
			});
		}
		else
			this.field.val($('<div/>').html(properties.value || '').text());

		this.text.html(this.field.val() || '&nbsp;');

		$('<br/>')
			.addClass('clear')
			.appendTo(self.field_container);

		this.button_add = $('<span/>')
			.html('<span class="ui-icon ui-icon-triangle-1-s"></span>Add another value')
			.addClass('ui-button ui-state-default ui-corner-all')
			.click(function(e) { self.add_field(); e.preventDefault(); })

		if (properties._type == 'list') {
			this.button_add.appendTo(self.field_container);
		}

		if (properties._item_type in boto_web.env.models) {
			if (self.existing_only) {
				//self.button_new = $('<span/>')
				self.field.hide();
			}
			//else {
				self.button_new = $('<span/>')
					.html('<span class="ui-icon ui-icon-plusthick"></span>New ' + properties._item_type)
					.addClass('ui-button ui-state-default ui-corner-all')
					.appendTo(self.field_container);

				if (self.editing_template) {
					self.button_new = self.button_new.click(function(e) { self.add_field(); e.preventDefault(); });
					if (properties._type != 'list')
						self.button_new.hide();
				}
				else
					self.button_new = self.button_new.click(function(e) { boto_web.env.models[properties._item_type].create({callback: function() {self.init()}}); e.preventDefault(); });
			//}
		}

		$('<br/>')
			.addClass('clear')
			.appendTo(self.field_container);
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	textarea: function(properties, opts) {
		properties._tagName = 'textarea';
		properties.innerHTML = properties.value;
		properties.rows = properties.rows || 3;
		properties.cols = properties.cols || 48;
		boto_web.ui.forms._field.call(this, properties, opts);
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	bool: function(properties, opts) {
		properties.type = 'radio';
		boto_web.ui.forms._field.call(this, properties, opts);

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
	complex: function(properties, opts) {
		boto_web.ui.forms._field.call(this, properties, opts);

		var self = this;

		this.field_container.empty();

		$(properties.value).each(function() {
			if (!this.name) return;

			var inpt = null;
			if(self.opts.choices){
				inpt = new boto_web.ui.forms.dropdown({name: this.name, choices: self.opts.choices}).field.val(this.value || '');
			} else {
				inpt = new boto_web.ui.forms.text({name: this.name}).field.val(this.value || '');
			}

			$('<dl/>')
				.addClass('mapping')
				.append(
					$('<dt/>')
						.text(this.name),
					$('<dd/>').append(inpt)
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
	text: function(properties, opts) {
		var self = this;

		boto_web.ui.forms._field.call(this, properties, opts);
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	password: function(properties, opts) {
		var self = this;
		properties.type = 'password';

		boto_web.ui.forms._field.call(this, properties, opts);

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
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	dropdown: function(properties, opts) {
		properties._tagName = 'select';
		boto_web.ui.forms._field.call(this, properties, opts);
	},

	/**
	 * @param {Object} properties HTML node properties.
	 */
	date: function(properties, opts) {
		boto_web.ui.forms._field.call(this, properties, opts);
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

		this.field.val(this.field.val().replace('T', ' ').replace(/(\d+:\d+)(:\d+)?Z?.*/, '$1 GMT') || '');

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
	file: function(properties, opts) {
		if (properties.value) {
			return new boto_web.ui.forms.textarea(properties, opts);
		}
		properties.type = 'file';
		boto_web.ui.forms._field.call(this, properties, opts);

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
	picklist: function(properties, opts) {
		properties._tagName = 'select';
		properties.choices = [];

		boto_web.ui.forms._field.call(this, properties, opts);

		var self = this;

		if (self.editing_template)
			self.field = $(self.editing_template).attr('name', properties.name);

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
						self.text.html(value_text);

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
						var selection = $('<div/>')
							.addClass('clear')
							.attr('id', 'selection_' + id)
							.html('<span class="ui-icon ui-icon-closethick"></span> ' + name)
							.appendTo(self.field_container.find('.selections'))

						self.button_new.show();

						if (self.properties._type != 'list' && self.nested_objs.length >= 1) {
							var remove_field = function() {
								// Hide custom fields if an existing selection is chosen
								$(self.nested_objs).each(function() {
									$(this.node).siblings('br:eq(0)').remove();
									$(this.node).remove();
								});

								self.nested_objs = [];
								self.fields.pop();
							};

							remove_field();

							selection.find('span').click(function() {
								$(this).parent().remove();

								// Remove the editor corresponding to this object
								remove_field();

								// Add a blank editor
								self.add_field();

								self.button_new.hide();
							});
							self.button_new.click(function() {
								selection.find('span').click();
							});
						}
						else {
							selection.find('span').click(function() {
								var removable = 1;

								if (self.nested_objs.length) {
									removable = 0;
									self.nested_objs = $.map(self.nested_objs, function(o) {
										if (o.obj.id == id) {
											if (++removable == 1) {
												$(o.node).remove();
												try { $(o.node).siblings('br:eq(0)').remove(); } catch (e) {}
												return null;
											}
										}
										return o;
									});
								}

								if (removable == 1)
									$(this).parent().remove();
							});
						}

						if (self.editing_template) {
							self.model.get(id, function(obj) {
								self.add_field(obj);
							});
						}
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
										.html(obj[i].properties.name)
										.click(function(e){
											if (self.properties._type != 'list' && !self.opts.allow_multiple)
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

					self.button_add = $('<span/>');

					$('<div/>')
						.addClass('search_results')
						.appendTo(self.field_container);

					$('<strong/>')
						.text('Your selection' + ((self.properties._type == 'list' || self.opts.allow_multiple) ? 's' : '') + ':')
						.appendTo(self.field_container);
					$('<div/>')
						.addClass('selections')
						.appendTo(self.field_container);

					self.button_new
						.appendTo(self.field_container);

					if (self.editing_template)
						self.button_new.click(function(e) { self.add_field(); e.preventDefault(); });
					else
						self.button_new = self.button_new.click(function(e) { boto_web.env.models[properties._item_type].create({callback: function() {self.init()}}); e.preventDefault(); });

					if (properties._type != 'list' && self.properties.value)
						self.button_new.hide();

					$('<br/>')
						.addClass('clear')
						.appendTo(self.field_container);

					if (self.properties.value) {
						if (!$.isArray(self.properties.value))
							self.properties.value = [self.properties.value];

						$(self.properties.value).each(function() {
							self.model.get(this.id || this, function(obj) {
								add_selection(obj.id, obj.properties.name, obj);
							});
						});
					}

					self.field_container.data('get_value', function() {
						var val = [];

						if (self.nested_objs.length) {
							var good = true;

							$(self.nested_objs).each(function() {
								if (!this.submitted) {
									this.submit();
									good = false;
									return false;
								}
								else {
									val.push(this.obj.id);
								}
							});

							if (!good)
								return false;
						}
						// TODO decide whether selections should be loaded into nested objects...
						// if not then this should not be in an else
						else {
							self.field_container.find('.selections div').each(function() {
								val.push(this.id.replace('selection_', ''));
							});
						}

						if (val.length == 1)
							val = val[0];
						else if (val.length == 0)
							val = '';

						return val;
					});
			/*	}
			});
			*/
		}

		self.init();
	}
};

boto_web.ModelMeta.prototype.create = function(opts) { return new boto_web.ui.BaseModelEditor(this, undefined, opts); };

boto_web.Model.prototype.edit = function(opts) { return new boto_web.ui.BaseModelEditor(boto_web.env.models[this.name], this, opts); };
boto_web.Model.prototype.del = function(opts) { return new boto_web.ui.BaseModelDeletor(boto_web.env.models[this.name], this, opts); };

