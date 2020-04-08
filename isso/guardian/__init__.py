# -*- encoding: utf-8 -*-

# A guard without any reference to the database
class StatelessGuard:
	def __init__(self, config):
		self.conf = config
	
	def validate(self, uri, comment):
		if not self.conf.getboolean("enabled"):
			return True, ""
		return self._requiredFields(uri, comment)
	
	def _requiredFields(self, uri, comment):
		"""Checks required fields.
		@param comment : A JSON object
		@return True,empty string if everything is OK; else False and a reason"""
		# require email if :param:`require-email` is enabled
		if self.conf.getboolean("require-email") and not comment.get("email"):
			return False, "email address required but not provided"

		# require author if :param:`require-author` is enabled
		if self.conf.getboolean("require-author") and not comment.get("author"):
			return False, "author address required but not provided"
		
		return True,""
	
