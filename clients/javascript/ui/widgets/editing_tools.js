/**
 * @author    Ian Paterson
 * @namespace boto_web.ui.widgets.editing_tools
 */

/**
 * Displays object editing links based on the actions available to the user.
 *
 * @param node where to insert the icons.
 */
boto_web.ui.widgets.EditingTools = function(node, model) {
	var self = this;

	self.node = $(node);
	self.model = model;

	if ('delete' in self.model.methods)
		$('<li><a bwLink="delete"><span class="ui-icon ui-icon-trash"></span>Delete</a></li>').prependTo(self.node);

	if ('put' in self.model.methods)
		$('<li><a bwLink="edit"><span class="ui-icon ui-icon-pencil"></span>Edit</a></li>').prependTo(self.node);

	self.node.find('a').addClass('ui-button ui-state-default ui-corner-all');
};
