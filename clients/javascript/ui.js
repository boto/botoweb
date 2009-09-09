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

		boto_web.env.apis = $('api', data).map(function(){ return new boto_web.ui.api(this) })

		alert($.dump(boto_web.env.apis));
	},

	/**
	 * Builds the interface for a specific api.
	 *
	 * @param {Element} data The XML element defining this api.
	 * @constructor
	 */
	api: function(data) {
		var self = this;
		data = $(data);

		self.name = data.attr('name');
		self.href = $('href', data).text();
		self.methods = {};

		// Parse method names and descriptions
		$('methods *', data).each(function(){ self.methods[this.nodeName] = $(this).text() });

		self.properties = $('properties property', data).map(function(){
			var data = $(this);
			var property = {};

			// Pull attributes from the property node
			var map = {
				name: 'name',
				maxlength: 'max_length',
				min_value: 'min',
				max_value: 'max'
			};

			for (var i in map) {
				if (data.attr(map[i]) == undefined) continue;

				property[i] = data.attr(map[i]);
			}

			// Pull text content of children of the property node
			map = {
				label: 'description',
				default_value: 'default'
			};

			for (var i in map) {
				var node = $(map[i], data);
				if (!node.length) continue;
				property[i] = node.text();
			}

			// Get key value maps for multiple choice properties
			map = {
				choices: 'choice'
			};

			for (var i in map) {
				var nodes = $(map[i], data);
				if (!nodes.length) continue;
				property[i] = new Array();
				nodes.each(function(){
					property[i].push({value: $(this).attr('value'), text: $(this).text()});
				})
			}

			return property;
		});
	},

	///**
	 //* Generic interface for all field types.
	 //*
	 //* @param {Object} properties HTML node properties.
	 //*/
	//_field: function(properties) {
		//var self = this;
		//this.node = $('<div/>');
		//this.label = $('<label/>').text(properties._label || '');
		//this.field = $('<' + (properties._tagName || 'input') + '/>');
		//this.text = $('<span/>');

		//properties.id = properties.id || 'field_' + properties.name;

		//for (p in properties) {
			//var v = properties[p];

			//if (p.indexOf('_') == 0)
				//continue;

			////TODO More special cases needed (i.e. multiple choice items)
			//switch (p) {
				//case 'choices':
					//for (i in v) {
						//v[i].text = v[i].text || v[i].value;
						//var opt = $('<option/>').attr(v[i]);

						//this.field.append(opt)
					//}
					//break;
				//default:
					//this.field.attr(p, v);
			//}
		//}

		//if (properties._default) {
			//this.field.val(properties._default);
		//}

		//this.text.text(this.field.val());

		///**
		 //* Switches the
		 //*/
		//this.read_only = function(on) {
			//if (on || on == undefined) {
				//this.field_container.hide();
				//this.text.show();
			//}
			//else {
				//this.text.hide();
				//this.field_container.show();
			//}
		//}

		//this.field_container = $('<span/>').append(this.field);
		//this.node.append(this.label, this.field_container, this.text);
		//this.read_only();
	//},

	///**
	 //* @param {Object} properties HTML node properties.
	 //*/
	//textarea: function(properties) {
		//properties.innerHTML = properties.value;
		//boto_web.ui._field.call(this, properties);
	//},

	///**
	 //* @param {Object} properties HTML node properties.
	 //*/
	//text: function(properties) {
		//boto_web.ui._field.call(this, properties);
	//},

	///**
	 //* @param {Object} properties HTML node properties.
	 //*/
	//date: function(properties) {
		//boto_web.ui._field.call(this, properties);

		//this.datepicker = $(this.field).datepicker({
			//showOn: 'both',
			//showAnim: 'slideDown'
		//});

	//}
};
