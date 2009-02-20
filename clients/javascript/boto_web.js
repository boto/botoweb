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
	all: function(url, fnc){
		return boto_web.find(url, null, fnc);
	},

	//
	// Find items at this URL using optional filters
	// @param url: The URL to search at
	// @param filters: The Filters to apply (or null for none), this should be of the form {name: value, name2: value2}
	// @param fnc: The function to call back to
	//
	find: function(url, filters, fnc){
		// Apply the filters
		url += "?";
		for (filter in filters){
			url += filter + "=" + filters[filter] + "&";
		}

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

		$(data).find("property").each(function(){
			var value = null
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
			obj[$(this).attr('name')] = value;
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
			$(data).find("object").each(function(){
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
	save: function(url, data){
		var doc = document.implementation.createDocument("","objects",null);
		var obj = doc.createElement("object");
		doc.documentElement.appendChild(obj);
		for(pname in data){
			var prop = doc.createElement("property");
			$(prop).attr("name", pname);
			var pval = data[pname];
			prop.appendChild(boto_web.encode_prop(pval, doc));
			if(pval.constructor.toString().indexOf("Array") != -1){
				$(prop).attr("type", "List");
			} else if (pval.constructor.toString().indexOf("Class") != -1){
				$(prop).attr("type", "Reference");
			}
			obj.appendChild(prop);
		}
		$.ajax({
			type: "PUT",
			url: url,
			processData: false,
			data: doc
		});
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
		}
		return ret;
	}
};
