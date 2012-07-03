from django.test import TestCase


class BlogTest(TestCase):
	def test_get_blog(self):
		url = '/blog/'
		response = self.client.get(url)
		self.assertContains(response, 'Blog', status_code=200)
		self.assertTrue(response, 'is_blog')

