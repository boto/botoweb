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
