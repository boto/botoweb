// Copyright (c) 2009 Chris Moyer http://kopertop.blogspot.com
//
// Permission is hereby granted, free of charge, to any person obtaining a
// copy of this software and associated documentation files (the
// "Software"), to deal in the Software without restriction, including
// without limitation the rights to use, copy, modify, merge, publish, dis-
// tribute, sublicense, and/or sell copies of the Software, and to permit
// persons to whom the Software is furnished to do so, subject to the fol-
// lowing conditions:
//
// The above copyright notice and this permission notice shall be included
// in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
// OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
// ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
// SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
// WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
// IN THE SOFTWARE.

//
// Javascript API for boto_web searching
//
var boto_web = {
	ajax: {
		cachedRequests: {},
		manager: $.manageAjax.create("cacheQueue", { queue: true, cacheResponse:true, preventDoubbleRequests: false, maxRequests: 3 }),
		stop: function(name, id){
			boto_web.ajax.cachedRequests = {};
			boto_web.ajax.manager.abort(name, id);
		},
		get: function(url, callback){
			var ajaxID = 'GET_'+ url.replace(/\./g, '_');
			var cachedRequests = boto_web.ajax.cachedRequests;
			if(cachedRequests[ajaxID]){
				cachedRequests[ajaxID].push(callback);
			} else {
				cachedRequests[ajaxID] = [callback];

				boto_web.ajax.manager.add({
					success: function(data){
						for(cbnum in cachedRequests[ajaxID]){
							cachedRequests[ajaxID][cbnum](data);
						}
						delete cachedRequests[ajaxID];
					},
					url: url
				});
			}
		}
	},

	//
	// Get all items at this url
	//
	all: function(url, obj_name, fnc){
		return boto_web.find(url, null, obj_name, fnc);
	},

	//
	// Find items at this URL using optional filters
	// @param url: The URL to search at
	// @param filters: The Filters to apply (or null for none), this should be of the form {name: value, name2: value2}
	// @param fnc: The function to call back to
	//
	find: function(url, filters, obj_name, fnc){
		// Apply the filters
		url += "?";
		for (filter in filters){
			url += filter + "=" + filters[filter] + "&";
		}

		var page = 0;
		var process = function(xml){
			var data = [];
			$(xml).find(obj_name).each(function(){
				var obj = boto_web.parseObject(this);
				if(obj.length > 0){
					data.push(obj);
				}
			});
			url = $(xml).find('link[rel=next]').attr('href');

			// Get the next page
			if (fnc(data, page++) && url)
				boto_web.ajax.get(url, process);
		}

		return boto_web.ajax.get(url, process);
	},

	//
	// Advanced query searching
	// @param url: The URL to search at
	// @param query: The Query to use, this must be an array of tuples [name, op, value]
	// 		if "value" is a list, this is treated as an "or" and results in ["name" op "value" or "name" op "value"]
	// 		"op" must be one of the following: (=|>=|<=|!=|<|>|starts-with|ends-with|like)
	// @param fnc: The callback function
	//
	query: function(url, query, obj_name, fnc){
		// Build the query string
		parts = [];
		for (query_num in query){
			query_part = query[query_num];
			name = query_part[0];
			op = query_part[1];
			value = query_part[2];

			if(value.constructor.toString().indexOf("Array") != -1){
				parts.push('["' + name + '","' + op + '",["' + value.join('","') + '"]]');
			} else {
				parts.push('["' + name + '","' + op + '","' + value + '"]');
			}
		}

		url += "?query=[" + escape(parts.join(",") + "]");

		var page = 0;
		var process = function(xml){
			var data = [];
			$(xml).find(obj_name).each(function(){
				var obj = boto_web.parseObject(this);
				if(obj.length > 0){
					data.push(obj);
				}
			});
			url = $(xml).find('link[rel=next]').attr('href');

			// Get the next page
			if (fnc(data, page++) && url)
				boto_web.ajax.get(url, process);
		}

		return boto_web.ajax.get(url, process);
	},

	//
	// Function: parseObject
	// Parse this XML into an object
	//
	parseObject: function(data){
		var obj = {};
		obj.length = 0;
		obj.id = $(data).attr('id');
		obj.model = data.tagName;

		$(data).children().each(function(){
			var value = null;
			if($(this).attr("type") == "reference"){
				value = {
					name: this.tagName,
					type: 'reference',
					href: $(this).attr("href"),
					id: $(this).attr("id"),
					item_type: $(this).attr('item_type')
				};
			}
			else if($(this).children().length){
				value = [];
				$(this).children().each(function() {
					value.push({
						name: $(this).attr('name'),
						type: $(this).attr('type'),
						value: $(this).text()
					});
				});
			}
			else {
				value = $(this).text();
			}
			if (obj[this.tagName]) {
				if (!$.isArray(obj[this.tagName]))
					obj[this.tagName] = [obj[this.tagName]];
				obj[this.tagName].push(value);
			}
			else {
				obj[this.tagName] = value;
			}
			obj.length++;
		});
		return obj;
	},

	//
	// Function: get_by_id
	// Find a specific object by ID
	//
	get_by_id: function(url, id, fnc){
		boto_web.ajax.get(url + "/" + id, function(data){
			$(data).children().each(function(){
				var curobj = boto_web.parseObject(this);
				if(curobj.length > 0){
					fnc(curobj);
				}
			});
		});
	},

	//
	// Functon: save
	// Save this ticket, or create a new one
	// the Data string is a simple class mapping
	// which is then converted into the proper XML document
	// to be sent to the server
	//
	save: function(url, obj_name, data, method, fnc){
		var doc = document.implementation.createDocument("", obj_name, null);
		var obj = doc.documentElement;
		for(pname in data){
			var pval = data[pname];

			if (pval == undefined)
				continue;

			if (!(pname in boto_web.env.models[obj_name].prop_map)) {
				console.log(pname + ' ' + obj_name);
				continue;
			}

			var type = boto_web.env.models[obj_name].prop_map[pname]._type;

			var list = true;

			if(pval.constructor.toString().indexOf("Array") == -1){
				pval = [pval];
				list = false;
			}

			// Force entire complexType to be encoded at once
			if (type == 'complexType')
				pval = [pval];
			else
				type = boto_web.env.models[obj_name].prop_map[pname]._item_type || type;

			$(pval).each(function() {
				if (list && this == '')
					return;

				var prop = doc.createElement(pname);

				// Modifies prop in place
				boto_web.encode_prop(this, prop, type);

				$(prop).attr("type", type);
				/*
				if(this.constructor.toString().indexOf("Array") != -1){
					$(prop).attr("type", "List");
				} else if (this.constructor.toString().indexOf("Class") != -1){
					$(prop).attr("type", "Reference");
				}
				else if (/\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?/.test(this)){
					$(prop).attr("type", "dateTime");
				}
				else {
					$(prop).attr("type", "string");
				}
				*/
				obj.appendChild(prop);
			});
		}

		//DEBUG
		alert(url + "\n\n" + (new XMLSerializer()).serializeToString(doc));
		fnc({status: 201, getResponseHeader: function() { return '123' ;}});
		return

		opts = {
			url: url,
			processData: false,
			data: doc
		}
		if(method){
			opts.type = method;
		} else {
			opts.type = "PUT";
		}

		if(fnc){
			opts.complete = fnc;
		}
		$.ajax(opts);
	},

	//
	// Function: encode_prop
	// Encode the property into an XML document object
	//
	encode_prop: function(prop, doc, type){
		var ret = null;
		if (prop == undefined)
			return null;
		if(type == 'complexType') {
			var items = [];
			for(var x=0; x < prop.length; x++){
				item = prop[x];
				var prop_item = $(doc).clone();
				boto_web.encode_prop(item, prop_item);
				items.push(prop_item);
			}
			$(items).each(function() { $(doc).append(this); });
		}
		else if(prop.constructor.toString().indexOf("Array") != -1){
			ret = $('<items/>').appendTo(doc);
			for(var x=0; x < prop.length; x++){
				item = prop[x];
				var prop_item = $("<item/>").appendTo(ret);
				boto_web.encode_prop(item, prop_item);
			}
		}
		else if(prop.constructor.toString().indexOf("Object") != -1){
			$(doc).text(prop.value.toString());
			$(doc).attr({type: "string", name: prop.name});
		}
		else {
			$(doc).text(prop.toString());
			$(doc).attr("type", "string");
		}
		return $(doc);
	},

	//
	// Function: del
	// Delete this object
	//
	del: function(url, fnc){
		$.ajax({
			type: "DELETE",
			url: url,
			complete: fnc
		});
	},

	count: function(url, fnc){
		$.ajax({
			type: "HEAD",
			url: url,
			complete: function(data) {
				fnc(data.getResponseHeader('Count'));
			}
		});
	},

	//
	// Class: Environment
	// This is the Environment class, intended to be instantiated
	// i.e: env = new boto_web.Environment("data");
	// Note that the loading of the routes and users happens asynchronously,
	// so if you need to make sure everything is loaded before you use it,
	// pass in a callback:
	// new boto_web.Environment("data", function(env){
	//     alert(env.user.username);
	// });
	//
	// @param base_url: The base URL that we are operating on
	// @param fnc: Optional callback function to call after we finish loading
	//
	Environment: function(base_url, fnc, opts){
		// This is to support some weird things that
		// jQuery does while doing ajax processing, if
		// we ever need to refer to the Environment
		// object, we use "self"
		var self = this;
		self.base_url = base_url;
		self.user = null;
		self.opts = opts;
		self.routes = [];
		self.models = {};


		// __init__ object
		// Get our route info
		boto_web.ajax.get(self.base_url, function(xml){
			// Setup our name
			self.name = $(xml).find("Index").attr("name");
			// Set our routes and model APIs
			$(xml).find('api').map(function(){
				var mm = new boto_web.ModelMeta(this);
				var route = {
					href: mm.href,
					obj: mm.name
				};
				mm.href = mm.href;
				self.routes.push(route);
				eval("self.models." + mm.name + " = mm");
			});
			// Set our user object
			$(xml).find("User").each(function(){
				var obj = boto_web.parseObject(this);
				if(obj.length > 0){
					self.user = obj;
				}
			});

			if(fnc){ fnc(self); }
		});
	},

	//
	// Base model object
	// This shouldn't ever be called directly
	//
	ModelMeta: function(xml){
		var self = this;
		xml = $(xml);

		self._DEBUG_MODEL_INSTANCE = 1;
		self.name = xml.attr('name');
		self.href = $('href', xml).text();
		self.methods = {};
		self._cache = {};
		self.cache_timeouts = {};
		self.prop_map = {};
		self.data_tables = {};

		// Parse method names and descriptions
		$('methods *', xml).each(function(){ self.methods[this.nodeName] = $(this).text() });

		self.properties = $('properties property', xml).map(function(){
			var xml = $(this);
			var property = {};

			// Pull attributes from the property node
			var map = {
				_DEBUG_MODEL_PROPERTIES: 1,
				name: 'name',
				_type: 'type',
				_item_type: 'item_type',
				maxlength: 'max_length',
				min_value: 'min',
				max_value: 'max',
				_perm: 'perm'
			};

			for (var i in map) {
				if (xml.attr(map[i]) == undefined) continue;
				property[i] = xml.attr(map[i]);
			}

			if (property._perm)
				property._perm = property._perm.split(' ');
			else
				property._perm = [];

			// Pull text content of children of the property node
			map = {
				_label: 'description',
				_default_value: 'default'
			};

			for (var i in map) {
				var node = $(map[i], xml);
				if (!node.length) continue;
				property[i] = node.text();
			}

			if (!property._label)
				property._label = property.name;

			// Get key value maps for multiple choice properties
			map = {
				choices: 'choice'
			};

			for (var i in map) {
				var nodes = $(map[i], xml);
				if (!nodes.length) continue;
				property[i] = [];
				nodes.each(function(){
					property[i].push({value: $(this).attr('value'), text: $(this).text()});
				});
			}

			self.prop_map[property.name] = property;

			return property;
		});

		this.find = function(filters, fnc){
			var self = this;
			boto_web.find(boto_web.env.base_url + this.href, filters, $.map(boto_web.env.routes, function(m) { return m.obj }).join(', '), function(data, page){
				if(fnc){
					var objects = [];
					for(var x=0; x < data.length; x++){
						var model = boto_web.env.models[data[x].model];
						objects[x] = new boto_web.Model(model.href, model.name, data[x]);
					}
					return fnc(objects, page);
				}
			});
		}

		this.query = function(query, fnc){
			var self = this;
			boto_web.query(boto_web.env.base_url + this.href, query, $.map(boto_web.env.routes, function(m) { return m.obj }).join(', '), function(data, page){
				if(fnc){
					var objects = [];
					for(var x=0; x < data.length; x++){
						var model = boto_web.env.models[data[x].model];
						objects[x] = new boto_web.Model(model.href, model.name, data[x]);
					}
					return fnc(objects, page);
				}
			});
		}
		this.all = function(fnc){
			return this.find([], fnc);
		}

		this.count = function(fnc){
			if (self.obj_count)
				return fnc(self.obj_count);

			boto_web.count(boto_web.env.base_url + this.href, function(count) {
				self.obj_count = count;
				fnc(count);
			});
		}

		this.cache = function(obj) {
			self._cache[obj.id] = obj;
			clearTimeout(self.cache_timeouts[obj.id]);
			self.cache_timeouts[obj.id] = setTimeout(function() {
				delete self._cache[obj.id];
			}, 10000);
			return self._cache[obj.id];
		}


		this.get = function(id, fnc){
			var self = this;
			if (self._cache[id]) {
				fnc(self._cache[id]);
				return;
			}
			boto_web.get_by_id(boto_web.env.base_url + self.href, id, function(obj){
				if(obj){
					return fnc(self.cache(new boto_web.Model(self.href, self.name, obj)));
				}
			});
		}

		this.save = function(data, fnc){
			ref = boto_web.env.base_url + this.href;
			method = "POST";
			if("id" in data){
				delete self._cache[data.id];
				ref += ("/" + data.id);
				delete(data['id']);
				method = "PUT";
			}
			delete self._cache[data.id];
			return boto_web.save(ref, this.name, data, method, fnc);
		}

		//
		// Delete this object
		//
		this.del = function(id, fnc){
			ref = this.href;
			return boto_web.del(boto_web.env.base_url + ref + "/" + id, function(x) {
				$(self.data_tables[id]).each(function() {
					this.table.del(this.row);
				});
				delete self.data_tables[id];
				delete self._cache[id];
				return fnc(x);
			});
		}

	},
	//
	// Model wrapper
	//
	Model: function(href, name, properties){
		var self = this;

		self._DEBUG_OBJECT_INSTANCE = 1;
		self.href = href;
		self.name = name;
		self.properties = properties;
		self.id = properties.id;

		self.follow = function(property, fnc, filters) {
			var props = self.properties[property];

			if (!$.isArray(props))
				props = [props];

			$(props).each(function() {
				if (this.id != undefined) {
					if (this.item_type) {
						boto_web.env.models[this.item_type].get(this.id, function(obj) {
							return fnc([obj]);
						});
					}
					return;
				} else {
					boto_web.query(boto_web.env.base_url + self.href + '/' + self.id + '/' + this.href, filters, '*>*[id]', function(data) {
						if(fnc){
							var objects = [];
							for(var x=0; x < data.length; x++){
								var model = boto_web.env.models[data[x].model];
								objects[x] = new boto_web.Model(model.href, model.name, data[x]);
							}
							return fnc(objects);
						}
					});
				}
			});
		}
	},

	//
	// Simple Initialization script
	// which handles the everyday setup that
	// most of our apps will have to do
	// We make available the environment object
	// in boto_web.env
	//
	// href: the location of the API root
	//
	init: function(href, opts, default_ui){
		boto_web.ui.use_default = default_ui;
		boto_web.env = new boto_web.Environment(href, boto_web.ui.init, opts);
	}
};

//
// Global Ajax retrying on 408
//
$(document).ajaxError(function(e, request, opts, err){
	if(request.status == 408){
		$.ajax(opts);
	}
});
