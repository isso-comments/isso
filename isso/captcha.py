import logging
import requests


logger = logging.getLogger("isso")


class CaptchaProvider(object):
	name = "none"
	default_script_url = ""
	default_response_field = "captcha-response"

	def __init__(self, conf):
		self.conf = conf

	def get(self, key, fallback=""):
		return self.conf.get("captcha", key, fallback=fallback).strip()

	def response_field(self):
		# If `captcha-response-field` is defined in the config but left empty, `get()` will return an empty string, 
		# so we need to use the default value in that case. fallback works only when the field is not defined at all.
		return self.get("captcha-response-field", fallback=self.default_response_field) or self.default_response_field

	def site_key(self):
		return self.get("captcha-site-key")

	def secret_key(self):
		return self.get("captcha-secret-key")

	def widget_html(self):
		raise NotImplementedError()

	def script_url(self):
		configured = self.get("captcha-script-url")
		if configured:
			return configured
		if self.is_configured() and self.default_script_url:
			return self.default_script_url
		return ""

	def is_configured(self):
		return bool(self.site_key() and self.secret_key())

	def verify(self, data):
		if not self.is_configured():
			return True

		token = data.get(self.response_field(), "")
		if not token:
			return False

		return self.verify_token(token)

	def verify_token(self, token):
		raise NotImplementedError()

	def config(self):
		return {
			"captcha-enabled": self.is_configured(),
			"captcha-provider": self.name,
			"captcha-script-url": self.script_url(),
			"captcha-instance-url": self.get("captcha-instance-url"),
			"captcha-site-key": self.site_key(),
			"captcha-widget-html": self.widget_html(),
			"captcha-response-field": self.response_field(),
		}

	def template_context(self):
		config = self.config()
		return {
			"captcha_enabled": config["captcha-enabled"],
			"captcha_provider": config["captcha-provider"],
			"captcha_script_url": config["captcha-script-url"],
			"captcha_instance_url": config["captcha-instance-url"],
			"captcha_site_key": config["captcha-site-key"],
			"captcha_widget_html": config["captcha-widget-html"],
			"captcha_response_field": config["captcha-response-field"],
		}

	def post_json_success(self, url, payload):
		try:
			response = requests.post(url, data=payload, timeout=5)
			return bool(response.json().get("success"))
		except Exception:
			return False


class DisabledCaptchaProvider(CaptchaProvider):
	name = "none"

	def is_configured(self):
		return False

	def verify_token(self, token):
		return True

	def widget_html(self):
		return self.get("captcha-widget-html")


class CapCaptchaProvider(CaptchaProvider):
	name = "cap"
	default_script_url = "https://cdn.jsdelivr.net/npm/cap-widget@latest"
	default_response_field = "cap-token"

	def instance_url(self):
		return self.get("captcha-instance-url")

	def is_configured(self):
		return bool(super(CapCaptchaProvider, self).is_configured() and self.instance_url())

	def verify_token(self, token):
		verify_url = "%s/%s/siteverify" % (self.instance_url().rstrip("/"), self.site_key())
		return self.post_json_success(
			verify_url,
			{
				"secret": self.secret_key(),
				"response": token,
			},
		)

	def widget_html(self):
		configured = self.get("captcha-widget-html")
		if configured:
			return configured

		return "<cap-widget data-cap-api-endpoint=%s/%s/></cap-widget>" % (self.instance_url(), self.site_key())


class RecaptchaProvider(CaptchaProvider):
	name = "recaptcha"
	default_script_url = "https://www.google.com/recaptcha/api.js"
	default_response_field = "g-recaptcha-response"
	verify_url = "https://www.google.com/recaptcha/api/siteverify"

	def verify_token(self, token):
		return self.post_json_success(
			self.verify_url,
			{
				"secret": self.secret_key(),
				"response": token,
			},
		)

	def widget_html(self):
		configured = self.get("captcha-widget-html")
		if configured:
			return configured
		return '<div class="g-recaptcha" data-sitekey=%s></div>' % self.site_key()

class HcaptchaProvider(CaptchaProvider):
	name = "hcaptcha"
	default_script_url = "https://js.hcaptcha.com/1/api.js"
	default_response_field = "h-captcha-response"
	verify_url = "https://api.hcaptcha.com/siteverify"

	def verify_token(self, token):
		return self.post_json_success(
			self.verify_url,
			{
				"secret": self.secret_key(),
				"response": token,
			},
		)

	def widget_html(self):
		configured = self.get("captcha-widget-html")
		if configured:
			return configured
		return '<div class="h-captcha" data-sitekey=%s></div>' % self.site_key()

def create_provider(conf):
	provider_name = conf.get("captcha", "captcha-provider", fallback="").strip().lower()

	providers = {
		"cap": CapCaptchaProvider,
		"recaptcha": RecaptchaProvider,
		"hcaptcha": HcaptchaProvider,
	}

	provider = providers.get(provider_name)
	if provider is None:
		logger.warning("Unknown captcha provider '%s'; captcha verification disabled", provider_name)
		return DisabledCaptchaProvider(conf)

	return provider(conf)
