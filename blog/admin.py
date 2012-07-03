from django.contrib import admin
from blog.models import BlogPost


class BlogPostAdmin(admin.ModelAdmin):
	fieldsets = (
		('Blog Posts', {'fields': ('title', 'author', 'url', 'summary', \
		'content', 'pub_date', 'visible', 'meta_description', 'pic_url', \
		'pic_alt_text')}),)
	list_display = ('title', 'url', 'pub_date', 'visible')


admin.site.register(BlogPost, BlogPostAdmin)
