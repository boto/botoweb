/**
 * @projectDescription This is an experimental and very unfinished JavaScript
 * library which will be capable of generating a full CRUD interface based on
 * an XML API definition.
 *
 * @author    Ian Paterson
 * @namespace boto_web.ui.js
 */

/**
 * CRUD interface for simplified web application implementation based on an XML
 * definition.
 */
boto_web.ui = {
	/**
	 * Loads and displays the appropriate API.
	 * @param {XMLDocument} data The boto_web application index definition.
	 */
	init: function(data) {
		data = $(data);

		//TODO Access a specific api
		//TODO Convert everything to JSON up front instead of passing along XML?
		var api = new boto_web.ui.api($('api[name=Publisher]', data));
	},

	/**
	 * Builds the interface for a specific api.
	 *
	 * @param {Element} data The XML element defining this api.
	 */
	api: function(data) {
		var self = this;
		data = $(data);

		this.name = data.attr('name');
		this.node = $('body').append($('<div/>'));
		this.node.append($('<h2/>').text(this.name));
		this.fields = new Array();

		this.node.append($('<button/>').text('Edit').click(function() { self.switch_method('put') }));
		this.node.append($('<button/>').text('View').click(function() { self.switch_method('get') }));

		/**
		 * Adds a field based on the XML definition.
		 *
		 * @param {Element} data The XML element defining this field.
		 */
		this.add_field = function(data) {
			data = boto_web.ui._get_html_properties(data);
			var field;

			//TODO Decide which field type is appropriate, for now just text fields
			switch (data._type) {
				case 'dateTime':
					field = new boto_web.ui.date(data);
					break;
				default:
					field = new boto_web.ui.text(data);
			}

			this.fields.push(field);
			this.node.append(field.node);
		}

		this.switch_method = function(method) {
			switch(method) {
				case 'post':
				case 'put':
					$.each(this.fields, function() { this.read_only(false) })
					break;
				default:
					$.each(this.fields, function() { this.read_only(true) })
			}
		}

		$('properties property', data).each(function(){
			self.add_field(this)
		});
	},

	/**
	 * Converts XML properties to a simple object of HTML element properties.
	 *
	 * @param {Element} xml_prop A property element generated from XML.
	 */
	_get_html_properties: function(xml_prop) {
		xml_prop = $(xml_prop);

		//TODO Implement all property conversions
		var html_props = {
			name: xml_prop.attr('name'),
			maxlength: xml_prop.attr('max_length'),
			_label: $('description', xml_prop).text(),
			_default: $('default', xml_prop).text(),
			_type: xml_prop.attr('type')
		};

		if ($('choices', xml_prop).length) {
			html_props._tagName = 'select';
			html_props.choices = new Array();

			$('choices choice', xml_prop).each(function() {
				html_props.choices.push({
					value: $(this).attr('value'),
					text: $(this).text()
				});
			})
		}

		return html_props;
	},

	/**
	 * Generic interface for all field types.
	 *
	 * @param {Object} properties HTML node properties.
	 */
	_field: function(properties) {
		var self = this;
		this.node = $('<div/>');
		this.label = $('<label/>').text(properties._label || '');
		this.field = $('<' + (properties._tagName || 'input') + '/>');
		this.text = $('<span/>');

		properties.id = properties.id || 'field_' + properties.name;

		for (p in properties) {
			var v = properties[p];

			if (p.indexOf('_') == 0)
				continue;

			//TODO More special cases needed (i.e. multiple choice items)
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
			if (on || on == undefined) {
				this.field_container.hide();
				this.text.show();
			}
			else {
				this.text.hide();
				this.field_container.show();
			}
		}

		this.field_container = $('<span/>').append(this.field);
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

	}
};
