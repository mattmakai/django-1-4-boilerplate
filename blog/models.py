from django.db import models


class Tag(models.Model):
  tag = models.CharField(max_length=40)
  post = models.ForeignKey('BlogPost')


class BlogPost(models.Model):
  title = models.CharField(max_length=70)
  author = models.CharField(max_length=100, default="Matthew Makai")
  url = models.SlugField(max_length=70)
  summary = models.CharField(max_length=200)
  content = models.TextField()
  pub_date = models.DateTimeField()
  twitter_post = models.CharField(max_length=130, blank=True, null=True)
  visible = models.BooleanField()
  meta_description = models.CharField(max_length=150)
  pic_url = models.URLField(max_length=100, blank=True, null=True)
  pic_alt_text = models.CharField(max_length=150, blank=True, null=True)
  def __unicode__(self):
    return str(self.title)
