// location binding system taken from:
// http://www.bennadel.com/blog/1520-Binding-Events-To-Non-DOM-Objects-With-jQuery.htm
// Our plugin will be defined within an immediately
// executed method.
(
	function( $ ){
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
			if (strLocation != window.location.href){

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
	}
)( jQuery );

//
// Set the current page and its subpage
// The page URI should be in the format of "#/page/sub_page/id"
// where both "sub_page" and "id" are optional
// Author: Chris Moyer
//
var currentPage = null;
function setPage(page_args){
	var original_args = page_args;
	page_args = page_args.split("/");
	if(page_args.length > 1){
		page_args.shift();
		page_name = page_args.shift();
		if(page_name != currentPage){
			$(".page").hide();
			$(".page#"+page_name).show().trigger("load");
			currentPage = page_name;

			$(".boto_web .header .nav a").removeClass('active');
			$(".boto_web .header .nav a[href=#" + original_args + "]").addClass('active');
		}
		// Load the sub page, if present
		sub_page_name = page_args.shift() || 'main';
		$(".content").hide();
		$(".content#"+page_name + "_" + sub_page_name).show().trigger("load", page_args);
	}
}

//
// Paging trigger
// Author: Chris Moyer
//
$(window.location).bind(
	"change",
	function(objEvent, objData){
		setPage(objData.currentHash);
	}
);
