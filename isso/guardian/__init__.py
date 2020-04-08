# -*- encoding: utf-8 -*-

import re
import logging

logger = logging.getLogger("isso")

# A guard without any reference to the database
class StatelessGuard:
	def __init__(self, config):
		self.conf = config
		if self.conf.get("uri-filter") :
			logger.info("StatelessGuard uses uri filter : '%s'",self.conf.get("uri-filter"))
			self.uriFilter = re.compile(self.conf.get("uri-filter"), re.IGNORECASE)
		else:
			self.uriFilter = None
	
	def validate(self, uri, comment):
		if not self.conf.getboolean("enabled"):
			return True, ""
		for func in (self._requiredFields, self._filterURI) :
			valid,reason = func(uri, comment)
			if not valid :
				return False,reason
		
		return True, ""
	
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
	
	def _filterURI(self, uri, comment) :
		# Filters the URI using matching against 'uri-filter' config
		if self.uriFilter and not self.uriFilter.fullmatch(uri) :
			return False,"uri is not in a valid format"
		else :
			return True,""
			
