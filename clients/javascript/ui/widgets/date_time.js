/**
 * @author    Ian Paterson
 * @namespace boto_web.ui.widgets.date_time
 */

/**
 * Displays formatted time stamps.
 *
 * @param node the node containing the search result template.
 */
boto_web.ui.widgets.DateTime = function(node, timestamp) {
	var self = this;

	self.node = $(node);

	if (!timestamp)
		return;

	var t = timestamp.match(/(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)/);

	if (t.length < 7)
		return

	// If the time is exactly midnight, assume that this is a date with unspecified time
	var has_time = (t[4]*1 || t[5]*1 || t[6]*1);

	if (has_time)
		self.date_time = new Date(Date.UTC(t[1],t[2] - 1,t[3],t[4],t[5],t[6]));
	else
		self.date_time = new Date(Date.UTC(t[1],t[2] - 1,t[3], 12, 0, 0));

	var time_str = '';

	if (has_time) {
		time_str = ' ' + ((self.date_time.getHours() % 12 || 12) + '').replace(/^(\d)$/, '0$1') + ':' +
			(self.date_time.getMinutes() + '').replace(/^(\d)$/, '0$1') + ' ' +
			((self.date_time.getHours() < 12 || self.date_time.getHours() == 0) ? 'AM' : 'PM');
	}

	self.node
		.empty()
		.text(
			(self.date_time.getMonth() + 1 + '').replace(/^(\d)$/, '0$1') + '/' +
			(self.date_time.getDate() + '').replace(/^(\d)$/, '0$1') + '/' +
			self.date_time.getFullYear() + time_str
		)
		// For sorting
		.prepend($('<span class="hidden"/>').text(timestamp))
		.attr('title', self.date_time.toLocaleDateString() + ((has_time) ? ' ' + self.date_time.toLocaleTimeString().replace(/:.. /, '') : ''));
};