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

	var settings = this.data_table.fnSettings();
	if (!settings) return;
	$(settings.aoColumns).each(function() {
		// Sort on raw value, not HTML markup
		this.bUseRendered = false;
		var col_class = false;

		// Expose dataTables functionality through classNames on the TH element
		//if (/\bno-sort\b/.test(this.nTh.className))
		//	this.bSortable = false;
		if (/\bno-search\b/.test(this.nTh.className))
			this.bSearchable = false;
		if (/\bhidden\b/.test(this.nTh.className))
			this.bVisible = false;
		if (/\b(col-\S+)\b/.test(this.nTh.className)) {
			col_class = true;
			this.sClass = RegExp.$1;
		}

		// For some reason the bSortable option is not handled very well by
		// dataTables, so this removes the sort functionality from the UI
		if (/\bno-sort\b/.test(this.nTh.className)) {
			$(this.nTh)
				.unbind()
				.css('cursor', 'default')
				.find('span').remove()
		}

		// Works opposite of how a rendering function should, but this is required
		// to function without modifying dataTables. Returns the original HTML after
		// setting the column's value to its text-only form.
		this.fnRender = function(t) {
			var html = t.aData[t.iDataColumn];
			var text = html.replace(/<[^>]*>/g, '');
			t.oSettings.aoData[t.iDataRow]._aData[t.iDataColumn] = text;
			if (col_class)
				t.nTd.className = 'cell-' + text.replace(/\s.*/, '');
			return html;
		}
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

	this.add_events = function() {
		table.find('tr')
			.addClass('selectable')
			.mousedown(function(e) {
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
				else if (e.ctrlKey || e.metaKey) {
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
	}

	this.append = function(rows) {
		if (!$.isArray(rows))
			return;

		var data = [];
		$(rows).each(function() {
			var item = [];
			$(this).find('td').each(function() {
				item.push($(this).html().replace(/^\s*|\s*$/g, ''));
			});
			data.push(item);
		});
		var raw_data = $.map(data, function(cols) {
			return [$.map(cols, function(col) { return col.replace(/<[^>]*>/g, ''); })]
		});

		if (data.length > 0) {
			this.data_table.fnAddData(data, true);
			this.add_events();
		}
	}

	this.reset = function() {
		this.data_table.fnClearTable();
	}
};


(function() {
	var sort_regex = new RegExp('[^\\w\\s\\d]|\\b(the|a|an)\\s+', 'gi');
	var sort_regex2 = new RegExp('^\\s*');
/**
 * Sorts strings while ignoring case, special characters, and HTML
 */
jQuery.fn.dataTableExt.oSort['string-asc']  = function(x,y) {
	x = x.replace(sort_regex, '').replace(sort_regex2, '').toLowerCase();
	y = y.replace(sort_regex, '').replace(sort_regex2, '').toLowerCase();
	return ((x < y) ? -1 : ((x > y) ?  1 : 0));
};

/**
 * Sorts strings while ignoring case, special characters, and HTML
 */
jQuery.fn.dataTableExt.oSort['string-desc'] = function(x,y) {
	x = x.replace(sort_regex, '').replace(sort_regex2, '').toLowerCase();
	y = y.replace(sort_regex, '').replace(sort_regex2, '').toLowerCase();
	return ((x < y) ?  1 : ((x > y) ? -1 : 0));
};
})();
