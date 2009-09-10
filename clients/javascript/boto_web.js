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

		return $.get(url, function(xml){
			var data = [];
			$(xml).find(obj_name).each(function(){
				var obj = boto_web.parseObject(this);
				if(obj.length > 0){
					data.push(obj);
				}
			});
			fnc(data);
		});
	},

	//
	// Advanced query searching
	// @param url: The URL to search at
	// @param query: The Query to use, this must be an array of tuples [name, op, value]
	// 		if "value" is a list, this is treated as an "or" and results in ["name" op "value" or "name" op "value"]
	// 		"op" must be one of the following: (=|>=|<=|!=|<|>|starts-with|ends-with|like)
	// @param fnc: The callback function
	//
	query: function(url, query, fnc){
		// Build the query string
		parts = [];
		for (query_num in query){
			query_part = query[query_num];
			name = query_part[0];
			op = query_part[1];
			value = query_part[2];

			if(value.constructor.toString().indexOf("Array") != -1){
				filter_parts = [];
				for(val in value){
					filter_parts.push("'" + name + "' " + op + " '" + value + "'");
				}
				parts.push("[" + filter_parts.join(" OR ") + "]");
			} else {
				parts.push("['" + name + "' " + op + " '" + value + "']");
			}
		}

		url += "?query=" + escape(parts.join(" intersection "));
		return $.get(url, function(xml){
			var data = [];
			$(xml).find("object").each(function(){
				var obj = boto_web.parseObject(this);
				if(obj.length > 0){
					data.push(obj);
				}
			});
			fnc(data);
		});
	},

	//
	// Function: parseObject
	// Parse this XML into an object
	//
	parseObject: function(data){
		var obj = {};
		obj.length = 0;
		obj.id = $(data).attr('id');

		$(data).children().each(function(){
			var value = null;
			if($(this).attr("type") == "Reference"){
				value = {
					className: $(this).find("object").attr("class"),
					id: $(this).find("object").attr("id"),
					fetch: function(url, fnc){
						boto_web.get_by_id(url, this.id, fnc);
					}
				};
			} else if ($(this).attr("type") == "List"){
				value = [];
				$(this).find("item").each(function(){
					var val_obj = $(this).find("object")[0];
					if(val_obj){
						value.push({
							className: $(val_obj).attr("class"),
							id: $(val_obj).attr("id"),
							fetch: function(url, fnc){
								boto_web.get_by_id(url, this.id, fnc);
							}
						});
					} else {
						value.push($(this).text());
					}
				});
			} else {
				value = $(this).text();
			}
			obj[this.tagName] = value;
			obj.length++;
		});
		return obj;
	},

	//
	// Function: get_by_id
	// Find a specific object by ID
	//
	get_by_id: function(url, id, fnc){
		$.get(url + "/" + id, function(data){
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
			var prop = doc.createElement(pname);
			var pval = data[pname];
			prop.appendChild(boto_web.encode_prop(pval, doc));
			if(pval.constructor.toString().indexOf("Array") != -1){
				$(prop).attr("type", "List");
			} else if (pval.constructor.toString().indexOf("Class") != -1){
				$(prop).attr("type", "Reference");
			}
			obj.appendChild(prop);
		}
		opts = {
			url: url,
			processData: false,
			data: doc
		}
		if(method){
			opts.type = method;
		} else {
			opts.method = "PUT";
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
	encode_prop: function(prop, doc){
		var ret = null;
		if(prop.constructor.toString().indexOf("Array") != -1){
			ret = doc.createElement("items");
			for(var x=0; x < prop.length; x++){
				item = prop[x];
				var prop_item = doc.createElement("item");
				prop_item.appendChild(boto_web.encode_prop(item, doc));
				ret.appendChild(prop_item);
			}
		} else if (prop.constructor.toString().indexOf("Object") != -1){
			ret = doc.createElement("object");
			$(ret).attr("id", prop.id);
			if(prop.className){
				$(ret).attr("class", prop.className);
			}
		} else {
			ret = doc.createTextNode(prop.toString());
			$(ret).attr("type", "string");
		}
		return ret;
	},

	//
	// Function: del
	// Delete this object
	//
	del: function(url, fnc){
		$.ajax({
			type: "DELETE",
			url: url,
			success: fnc
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
	Environment: function(base_url, fnc){
		// This is to support some weird things that
		// jQuery does while doing ajax processing, if
		// we ever need to refer to the Environment
		// object, we use "self"
		self = this;
		self.base_url = base_url;
		self.user = null;
		self.routes = [];
		self.models = {};


		// __init__ object
		// Get our route info
		$.get(self.base_url, function(xml){
			// Setup our name
			self.name = $(xml).find("Index").attr("name");
			// Set our APIs
			self.apis = $(xml).find('api').map(function(){ return new boto_web.API(this) });
			// Set our routes
			$.each(self.apis, function(){
				var route = {
					href: this.href,
					obj: this.name
				};
				self.routes.push(route);
				// Init this model object
				route_obj = new boto_web.ModelMeta(self.base_url + route.href, route.obj);
				eval("self.models." + route.obj + " = route_obj");
			});
			// Set our user object
			$(xml).find("user").each(function(){
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
	ModelMeta: function(href, name){
		mm = this;
		this.href = href;
		this.name = name;
		this.find = function(filters, fnc){
			boto_web.find(this.href, filters, this.name, function(data){
				if(fnc){
					var objects = [];
					for(var x=0; x < data.length; x++){
						objects[x] = new boto_web.Model(mm.href, data[x]);
					}
					fnc(objects);
				}
			});
		}

		this.query = function(query, fnc){
			boto_web.query(this.href, query, function(data){
				if(fnc){
					var objects = [];
					for(var x=0; x < data.length; x++){
						objects[x] = new boto_web.Model(mm.href, data[x]);
					}
					fnc(objects);
				}
			});
		}
		this.all = function(fnc){
			return this.find([], fnc);
		}

		this.get = function(id, fnc){
			boto_web.get_by_id(this.href, id, function(obj){
				if(obj){
					fnc(new boto_web.Model(this.href, obj));
				}
			});
		}

		this.save = function(data, fnc){
			ref = this.href;
			method = "POST";
			if("id" in data){
				ref += ("/" + data['id']);
				delete(data['id']);
				method = "PUT";
			}
			return boto_web.save(ref, this.name, data, method, fnc);
		}

		//
		// Delete this object
		//
		this.del = function(id, fnc){
			ref = this.href;
			return boto_web.del(ref + "/" + id, fnc);
		}

	},
	//
	// Model wrapper
	//
	Model: function(href, properties){
		this.href = href;
		this.properties = properties;
		this.id = properties.id;
	},

	//
	// Parses XML for a specific API.
	//
	API: function(xml) {
		var self = this;
		xml = $(xml);

		self.name = xml.attr('name');
		self.href = $('href', xml).text();
		self.methods = {};

		// Parse method names and descriptions
		$('methods *', xml).each(function(){ self.methods[this.nodeName] = $(this).text() });

		self.properties = $('properties property', xml).map(function(){
			var xml = $(this);
			var property = {};

			// Pull attributes from the property node
			var map = {
				name: 'name',
				maxlength: 'max_length',
				min_value: 'min',
				max_value: 'max'
			};

			for (var i in map) {
				if (xml.attr(map[i]) == undefined) continue;
				property[i] = xml.attr(map[i]);
			}

			// Pull text content of children of the property node
			map = {
				label: 'description',
				default_value: 'default'
			};

			for (var i in map) {
				var node = $(map[i], xml);
				if (!node.length) continue;
				property[i] = node.text();
			}

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

			return property;
		});
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
	init: function(href){
		$("div#home").hide();
		boto_web.env = new boto_web.Environment(href, boto_web.ui.init);
	}
};
