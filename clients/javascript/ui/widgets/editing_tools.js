/**
 * @author    Ian Paterson
 * @namespace boto_web.ui.widgets.editing_tools
 */

/**
 * Displays object editing links based on the actions available to the user.
 *
 * @param node where to insert the icons.
 */
boto_web.ui.widgets.EditingTools = function(node, model, actions) {
	var self = this;

	if (node.tagName != 'UL')
		node = $('<ul />').appendTo(node);

	self.node = $(node).addClass('widget-editing_tools');
	self.model = model;

	actions = actions || 'edit clone delete';
	actions = actions.split(/[, ]+/);

	for (i in actions.reverse()) {
		switch (actions[i]) {
			case 'create':
				if ('post' in self.model.methods)
					$('<li><a bwLink="create"><span class="ui-icon ui-icon-plus"></span>New ' + self.model.name + '</a></li>').prependTo(self.node);
				break;
			case 'clone':
				if ('post' in self.model.methods)
					$('<li><a bwLink="clone"><span class="ui-icon ui-icon-copy"></span>Clone ' + self.model.name + '</a></li>').prependTo(self.node);
				break;
			case 'delete':
				if ('delete' in self.model.methods)
					$('<li><a bwLink="delete"><span class="ui-icon ui-icon-trash"></span>Delete</a></li>').prependTo(self.node);
				break;
			case 'edit':
				if ('put' in self.model.methods)
					$('<li><a bwLink="edit"><span class="ui-icon ui-icon-pencil"></span>Edit</a></li>').prependTo(self.node);
				break;
		}
	}

	self.node.find('a').addClass('ui-button ui-state-default ui-corner-all');
};
