/**
 * @author    Ian Paterson
 * @namespace boto_web.ui.widgets.search
 */

/**
 * Generates a search form.
 *
 * @param node the node containing the search parameters.
 */
boto_web.ui.widgets.DataTable = function(table) {
	this.data_table = table.dataTable({
		bJQueryUI: true,
		oLanguage: {
			sSearch: 'Quick Search these results:',
			sLengthMenu: "Show _MENU_ records per page",
			sInfo: 'Showing _START_ to _END_ of _TOTAL_ results'
		},
		sDom: '<"fg-toolbar ui-widget-header ui-corner-tl ui-corner-tr ui-helper-clearfix"lTfr>t<"fg-toolbar ui-widget-header ui-corner-bl ui-corner-br ui-helper-clearfix"ip>',
		sPaginationType: 'full_numbers'
	});

	this.data_table.parent().find('.fg-toolbar.ui-corner-bl').append(
		$('<div/>')
			.addClass('selection-buttons')
			.append(
				$('<span/>')
					.addClass('fg-button ui-corner-tl ui-corner-bl ui-state-default')
					.text('Select All')
					.click(function() {
						table.find('tr').addClass('row_selected');
					}),
				$('<span/>')
					.addClass('fg-button ui-corner-tr ui-corner-br ui-state-default')
					.text('Deselect All')
					.click(function() {
						table.find('tr').removeClass('row_selected');
					})
			)
	);

	table.find('tr').mousedown(function(e) {
		if (e.shiftKey) {
			if (boto_web.ui.last_row) {
				var rows = $(this).parent().children();
				var i1 = rows.index($(this));
				var i2 = rows.index(boto_web.ui.last_row);

				rows.slice(Math.min(i1, i2), Math.max(i1, i2) + 1).each(function() {
					if (e.ctrlKey)
						$(this).removeClass('row_selected');
					else
						$(this).addClass('row_selected');
				});
			}
			e.preventDefault();
		}
		else if (e.ctrlKey) {
			e.preventDefault();
		}
		else {
			$(this).siblings('tr').removeClass('row_selected');
		}

		boto_web.ui.last_row = this;

		if (e.shiftKey)
			return;

		if ($(this).hasClass('row_selected'))
			$(this).removeClass('row_selected');
		else
			$(this).addClass('row_selected');
	});

	this.refresh = function() {
		this.data_table.fnGatherData();
		this.data_table.fnDraw();
	}
};

/**
 * Sorts strings while ignoring case, special characters, and HTML
 */
jQuery.fn.dataTableExt.oSort['string-asc']  = function(x,y) {
	x = x.replace(/<.*?>|[^\w\s\d]/g, '').toLowerCase();
	y = y.replace(/<.*?>|[^\w\s\d]/g, '').toLowerCase();
	return ((x < y) ? -1 : ((x > y) ?  1 : 0));
};

/**
 * Sorts strings while ignoring case, special characters, and HTML
 */
jQuery.fn.dataTableExt.oSort['string-desc'] = function(x,y) {
	x = x.replace(/<.*?>|[^\w\s\d]/g, '').toLowerCase();
	y = y.replace(/<.*?>|[^\w\s\d]/g, '').toLowerCase();
	return ((x < y) ?  1 : ((x > y) ? -1 : 0));
};
